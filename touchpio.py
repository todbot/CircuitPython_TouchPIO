# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Tod Kurt
#
# SPDX-License-Identifier: MIT
# pylint: disable=line-too-long
"""
`touchpio`
================================================================================

Capacitive touch sensing using Pico / RP2040 PIO, using touchio API


* Author(s): Tod Kurt

Implementation Notes
--------------------

**Hardware:**

This library only works on RP2040-based boards like the Raspberry Pi Pico, QTPY RP2040, and similar.

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

**References:**

 * Originally from `23 Feb 2023 picotouch_grid research <https://github.com/todbot/picotouch/tree/main/circuitpython/research/picotouch_grid/picotouch_grid>`_

 * Uses ideas from `PIO Capsense experiment / -scottiebabe 2022 <https://community.element14.com/products/raspberry-pi/f/forum/51242/want-to-create-a-capacitance-proximity-touch-sensor-with-a-rp2040-pico-board-using-pio/198662>`_

"""
# pylint: enable=line-too-long


__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/todbot/CircuitPython_TouchPIO.git"

import array
import rp2pio
import adafruit_pioasm


class TouchIn:
    """
    Read the state of a capacitive touch sensor.

    Usage::

      import touchpio
      import board

      touch = touchpio.TouchIn(board.GP2)
      while True:
          if touch.value:
              print("touched!")

    """

    _capsense_pio_code = adafruit_pioasm.assemble(
        """
    pull block           ; trigger a reading, get maxcount value from fifo, OSR contains maxcount
    set pindirs, 1       ; set GPIO as output
    set pins, 1          ; drive pin HIGH to charge capacitance
;    set x,24             ; wait time for pin charge
    set x,30             ; wait time for pin charge
charge:                  ; wait (24+1)*31 = 1085 cycles = 8.6us
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

    def __init__(self, touch_pin, max_count=10_000):
        """Use the TouchIn on the given pin.

        :param ~microcontroller.Pin pin: the pin to read from
        """
        self.max_count = max_count
        self.pio = rp2pio.StateMachine(
            TouchIn._capsense_pio_code,
            frequency=125_000_000,
            first_set_pin=touch_pin,
            jmp_pin=touch_pin,
        )
        self.max_count = 10_000
        self.buf_send = array.array("L", [max_count])  # 32-bit value
        self.buf_recv = array.array("L", [0])  # 32-bit value
        self.base_val = self.raw_value
        self.last_val = self.base_val
        """
    Minimum `raw_value` needed to detect a touch (and for `value` to be `True`).

    When the **TouchIn** object is created, an initial `raw_value` is read from the pin,
    and then `threshold` is set to be 200 + that value.

    You can adjust `threshold` to make the pin more or less sensitive::

      import board
      import touchpio

      touch = touchio.TouchIn(board.GP4)
      touch.threshold = 2000
        """
        self.threshold = self.base_val + 200

        if self.base_val == 0xFFFFFFFF:  # -1
            raise ValueError("No pulldown on pin; 1Mohm recommended")

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
