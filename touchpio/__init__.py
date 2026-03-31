# SPDX-FileCopyrightText: Copyright (c) 2023 Tod Kurt
#
# SPDX-License-Identifier: MIT
"""
`touchpio`
================================================================================

Capacitive touch sensing using Pico / Pico2 / RP2040 / RP2350 PIO.

* Author(s): Tod Kurt

**Hardware:**

Each touch pad connects to a GPIO pin with a ~1MΩ resistor to ground
(pull-down, the default) or to VCC (pull-up). Pads can be exposed copper,
foil tape, conductive fabric, etc.

This library only works on RP2040- or RP2350-based boards like the
Raspberry Pi Pico, QTPY RP2040, and similar.

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

**References:**

* Originally from `23 Feb 2023 picotouch_grid research
  <https://github.com/todbot/picotouch/tree/main/circuitpython/research/picotouch_grid/picotouch_grid>`_

* Uses ideas from `PIO Capsense experiment / -scottiebabe 2022
  <https://community.element14.com/products/raspberry-pi/f/forum/51242/want-to-create-a-capacitance-proximity-touch-sensor-with-a-rp2040-pico-board-using-pio/198662>`_


"""

from .touchin import TouchIn
from .touchin_multi import TouchInMulti
