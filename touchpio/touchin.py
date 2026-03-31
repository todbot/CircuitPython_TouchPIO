# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Tod Kurt
#
# SPDX-License-Identifier: MIT
"""Capacitive touch sensing for RP2040/RP2350 using PIO."""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/todbot/CircuitPython_TouchPIO.git"

import array

import adafruit_pioasm
import digitalio
import rp2pio


class TouchIn:
    """Read the state of a capacitive touch sensor.

    Usage::

      import touchpio
      import board

      touch = touchpio.TouchIn(board.GP2)
      while True:
          if touch.value:
              print("touched!")

    **Hardware:**

    This library only works on RP2040- or RP2350-based boards like the
    Raspberry Pi Pico, QTPY RP2040, and similar. Each pad should have a
    ~1MΩ resistor to ground (pull-down, the default) or to VCC (pull-up).

    **Software and Dependencies:**

    * Adafruit CircuitPython firmware for the supported boards:
      https://circuitpython.org/downloads

    **References:**

    * Originally from `23 Feb 2023 picotouch_grid research
      <https://github.com/todbot/picotouch/tree/main/circuitpython/research/picotouch_grid/picotouch_grid>`_

    * Uses ideas from `PIO Capsense experiment / -scottiebabe 2022
      <https://community.element14.com/products/raspberry-pi/f/forum/51242/want-to-create-a-capacitance-proximity-touch-sensor-with-a-rp2040-pico-board-using-pio/198662>`_

    """

    _pio_pulldown = adafruit_pioasm.assemble(
        """
    pull block           ; trigger a reading, get maxcount value from fifo, OSR contains maxcount
    set pindirs, 1       ; set GPIO as output
    set pins, 1          ; drive pin HIGH to charge capacitance
    set x,30             ; wait time for pin charge
charge:
    jmp x--, charge [31]
    mov x, osr           ; load maxcount value (10_000 usually)
    set pindirs, 0       ; set GPIO as input
timing:
    jmp x--, test        ; decrement x until timeout
    jmp done             ; we've timed out, so leave
test:
    jmp pin, timing      ; loop while pin is still high
done:
    mov isr, x           ; load ISR with count value in x
    push                 ; push ISR into RX fifo
    """
    )

    _pio_pullup = adafruit_pioasm.assemble(
        """
    pull block           ; trigger a reading, get maxcount value from fifo, OSR contains maxcount
    set pindirs, 1       ; set GPIO as output
    set pins, 0          ; drive pin LOW to discharge capacitance
    set x,30             ; wait time for pin discharge
discharge:
    jmp x--, discharge [31]
    mov x, osr           ; load maxcount value (10_000 usually)
    set pindirs, 0       ; set GPIO as input
timing:
    jmp x--, test        ; decrement x until timeout
    jmp done             ; we've timed out, so leave
test:
    jmp pin, done        ; if pin charged HIGH, we're done
    jmp timing           ; pin still LOW, keep looping
done:
    mov isr, x           ; load ISR with count value in x
    push                 ; push ISR into RX fifo
    """
    )

    def __init__(self, touch_pin, pull_type=digitalio.Pull.DOWN, max_count=10_000):
        """Use the TouchIn on the given pin.

        :param ~microcontroller.Pin touch_pin: the pin to read from
        :param pull_type: ``digitalio.Pull.DOWN`` (default) for external pull-down
            resistors, or ``digitalio.Pull.UP`` for external pull-up resistors.
        :param int max_count: the maximum possible pin value (a timeout effectively)

        """
        if pull_type not in {digitalio.Pull.DOWN, digitalio.Pull.UP}:
            raise ValueError("pull_type must be digitalio.Pull.DOWN or .UP")
        pio_code = (
            TouchIn._pio_pulldown if pull_type == digitalio.Pull.DOWN else TouchIn._pio_pullup
        )
        self.max_count = max_count
        self.last_val = 0
        self.pio = rp2pio.StateMachine(
            pio_code,
            frequency=125_000_000,
            first_set_pin=touch_pin,
            jmp_pin=touch_pin,
        )
        self.buf_send = array.array("L", [max_count])  # 32-bit value
        self.buf_recv = array.array("L", [0])  # 32-bit value
        self.base_val = self.raw_value
        self.threshold = self.base_val + 200

        pull_name = "pulldown" if pull_type == digitalio.Pull.DOWN else "pullup"
        if self.base_val == 0xFFFFFFFF:  # -1
            raise ValueError(f"No {pull_name} on pin; 1Mohm recommended")

    def _raw_read(self):
        self.pio.write(self.buf_send)
        self.pio.readinto(self.buf_recv)
        val = self.buf_recv[0]  # return 32-bit number from PIO
        if val > self.max_count:
            val = self.last_val
        self.last_val = val
        return val

    @property
    def raw_value(self):
        """ "The raw touch measurement as an `int`. (read-only)"""
        return self.max_count - self._raw_read()

    @property
    def value(self):
        """Whether the touch pad is being touched or not. (read-only)
        True when `raw_value` > `threshold`."""
        return self.raw_value > self.threshold
