# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2026 Tod Kurt
#
# SPDX-License-Identifier: MIT
"""Multi-channel parallel capacitive touch sensing for RP2040/RP2350 using PIO."""

import array
import time

import adafruit_pioasm
import digitalio
import microcontroller
import rp2pio


def _build_pio_asm(num_pins, pull_up=False, sample_delay=5):
    """Generate PIO assembly for single-cycle streaming with delay loop.

    Each sample iteration:
      1. ``in pins`` + autopush  (1 clock + autopush)
      2. Inner delay loop: set y, D → jmp y-- [31]
         = (D+1) × 32 clocks per sample
      3. ``jmp x--`` to next sample

    :param int sample_delay: Value loaded into Y for the delay loop
        (0–31).  Time per sample ≈ (sample_delay + 1) × 32 / freq.
        At 125 MHz:
          0 → 0.26µs,  1 → 0.51µs,  3 → 1.0µs,   5 → 1.5µs,
         10 → 2.8µs,  15 → 4.1µs,  31 → 8.2µs
    """
    if pull_up:
        return f"""
.program touch_multi
.wrap_target
    pull block
    mov x, osr

    ; ── discharge all pins LOW ──
    mov osr, ~ null
    out pindirs, {num_pins}
    mov osr, null
    out pins, {num_pins}

    set y, 30
discharge:
    jmp y-- discharge [31]

    ; ── release to input; pull-ups charge toward VCC ──
    mov osr, null
    out pindirs, {num_pins}

    ; ── stream snapshots with Y delay loop ──
sample:
    in pins, {num_pins}
    set y, {sample_delay}
delay:
    jmp y-- delay [31]
    jmp x-- sample
.wrap
"""
    else:
        return f"""
.program touch_multi
.wrap_target
    pull block
    mov x, osr

    ; ── charge all pins HIGH ──
    mov osr, ~ null
    out pindirs, {num_pins}
    mov osr, ~ null
    out pins, {num_pins}

    set y, 30
charge:
    jmp y-- charge [31]

    ; ── release to input; pull-downs discharge to GND ──
    mov osr, null
    out pindirs, {num_pins}

    ; ── stream snapshots with Y delay loop ──
sample:
    in pins, {num_pins}
    set y, {sample_delay}
delay:
    jmp y-- delay [31]
    jmp x-- sample
.wrap
"""


class TouchInMulti:
    """Parallel capacitive touch reader for up to 16 channels on RP2040/RP2350.

    Uses a single PIO state machine to read up to 16 capacitive touch pads
    simultaneously, streaming pin snapshots via autopush with a tunable
    inter-sample delay.

    **Hardware:**

    Each pad connects to a contiguous GPIO with a ~1MΩ resistor to ground
    (pull-down, the default) or to VCC (pull-up). Pads are exposed copper,
    foil tape, conductive fabric, etc.

    :param first_pin: The first GPIO pin (a ``microcontroller.Pin`` or
        ``board`` pin). Channels use contiguous GPIOs starting here.
    :param int num_pins: Number of touch channels (1–16).
    :param pull_type: ``digitalio.Pull.DOWN`` (default) for external
        pull-down resistors, or ``digitalio.Pull.UP`` for external
        pull-up resistors.
    :param int num_samples: Number of discharge snapshots per scan.
        Default 50.
    :param int sample_delay: PIO inter-sample delay (0–31).  Controls
        time between snapshots: (sample_delay + 1) × 256ns @ 125 MHz.
        Lower values → finer time resolution, but the measurement
        window (num_samples × time_per_sample) must cover your RC
        discharge curve.  Default 5 → ~1.5µs per sample.
    :param int touch_threshold: Raw count above baseline to register
        a touch.  Scale this with num_samples. Default 5.

    .. code-block:: python

        import board
        import digitalio
        from touchpio import TouchInMulti

        touch = TouchInMulti(first_pin=board.GP0, num_pins=8)
        touch.calibrate()

        while True:
          values = touch.read()
          for i, v in enumerate(values):
            if v > 0:
              print(f"Pad {i}: {v}")

    """

    def __init__(  # noqa: PLR0913 PLR0917
        self,
        first_pin,
        num_pins=8,
        pull_type=digitalio.Pull.DOWN,
        num_samples=50,
        sample_delay=3,
        touch_threshold=3,
    ):
        if num_pins < 1 or num_pins > 16:
            raise ValueError("num_pins must be 1–16")
        if sample_delay < 0 or sample_delay > 31:
            raise ValueError("sample_delay must be 0–31")
        if pull_type not in {digitalio.Pull.DOWN, digitalio.Pull.UP}:
            raise ValueError("pull_type must be digitalio.Pull.DOWN or .UP")

        self._num_pins = num_pins
        self._pull_up = pull_type == digitalio.Pull.UP
        self._pull_type = pull_type
        self._touch_threshold = touch_threshold
        self._num_samples = num_samples
        self._sample_delay = sample_delay
        self._baseline = [0] * num_pins
        self._pin_mask = (1 << num_pins) - 1

        # TX: single word (PIO pulls once). RX: num_samples words.
        self._tx = array.array("I", [num_samples - 1])
        self._rx = array.array("I", [0] * num_samples)

        # Pre-compute per-pin bit masks
        self._masks = [1 << p for p in range(num_pins)]

        # Assemble PIO
        pio_src = _build_pio_asm(num_pins, pull_up=self._pull_up, sample_delay=sample_delay)
        program = adafruit_pioasm.Program(pio_src)

        kwargs = dict(program.pio_kwargs)
        for key in ("in_shift_right", "out_shift_right", "auto_push", "push_threshold"):
            kwargs.pop(key, None)

        self._sm = rp2pio.StateMachine(
            program.assembled,
            frequency=125_000_000,
            first_out_pin=first_pin,
            out_pin_count=num_pins,
            first_in_pin=first_pin,
            in_pin_count=num_pins,
            pull_in_pin_up=0,
            pull_in_pin_down=0,
            in_shift_right=False,
            out_shift_right=True,
            auto_push=True,
            push_threshold=num_pins,
            **kwargs,
        )

    def deinit(self):
        """Release the PIO state machine."""
        self._sm.deinit()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.deinit()

    @property
    def num_pins(self):
        return self._num_pins

    @property
    def pull_type(self):
        return self._pull_type

    @property
    def num_samples(self):
        return self._num_samples

    @property
    def sample_delay(self):
        """PIO delay loop count (0–31). Time per sample ≈ (value+1) × 256ns."""
        return self._sample_delay

    @property
    def touch_threshold(self):
        return self._touch_threshold

    @touch_threshold.setter
    def touch_threshold(self, value):
        self._touch_threshold = value

    # ── Core scan ────────────────────────────────────────────────────────

    def scan_raw(self):
        """Perform one charge-discharge scan.

        Returns a list of ints (length ``num_pins``).  Each value is
        the number of snapshots where that pin was still in its
        charged state, proportional to pad capacitance.
        """
        self._sm.clear_rxfifo()
        self._sm.write_readinto(self._tx, self._rx)

        buf = self._rx
        mask = self._pin_mask
        invert = self._pull_up
        n = self._num_samples
        masks = self._masks
        counts = [0] * self._num_pins

        if invert:
            for i in range(n):
                buf[i] = (~buf[i]) & mask

        # Per-pin counting with early exit (discharge is monotonic)
        for pin in range(self._num_pins):
            m = masks[pin]
            c = 0
            for i in range(n):
                if buf[i] & m:
                    c += 1
                else:
                    break
            counts[pin] = c

        return counts

    # ── Calibration ──────────────────────────────────────────────────────

    def calibrate(self, num_samples=16):
        """Set baseline from the average of ``num_samples`` untouched scans."""
        accum = [0] * self._num_pins
        for _ in range(num_samples):
            raw = self.scan_raw()
            for i in range(self._num_pins):
                accum[i] += raw[i]
            time.sleep(0.005)
        self._baseline = [a // num_samples for a in accum]

    @property
    def baseline(self):
        return list(self._baseline)

    def read(self):
        """Read capacitance deltas above baseline.

        Returns a list of ints (length ``num_pins``).  Zero means
        untouched; positive values indicate a touch.
        """
        raw = self.scan_raw()
        return [max(0, raw[i] - self._baseline[i]) for i in range(self._num_pins)]

    def touched(self):
        vals = self.read()
        return [v > self._touch_threshold for v in vals]

    def touched_pins(self):
        vals = self.read()
        return [i for i in range(self._num_pins) if vals[i] > self._touch_threshold]

    def touched_bitmap(self):
        vals = self.read()
        bm = 0
        for i in range(self._num_pins):
            if vals[i] > self._touch_threshold:
                bm |= 1 << i
        return bm

    # to match as closely as we can to `touchpio`:

    def _raw_values(self):
        return self.read()

    def values(self):
        return self.touched()
