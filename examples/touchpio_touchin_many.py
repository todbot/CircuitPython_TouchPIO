# SPDX-FileCopyrightText: Copyright (c) 2023 Tod Kurt
#
# SPDX-License-Identifier: Unlicense
"""
touchpio_touchin_many.py

touchpio test with 8 pads.
Note this uses up all PIO state machines, showing why TouchPIO for single
pins isn't that useful. Use `touchio` instead.
"""

import time

import board
import digitalio

import touchpio

pull_type = digitalio.Pull.UP
# pull_type = digitalio.Pull.DOWN

touch_pins = (board.GP0, board.GP1, board.GP2, board.GP3,
              board.GP4, board.GP5, board.GP6, board.GP7, )  # fmt: skip

touchins = []
for pin in touch_pins:
    touchin = touchpio.TouchIn(pin, pull_type=pull_type)
    touchins.append(touchin)

while True:
    print(" ".join(["%d" % t.value for t in touchins]))
    time.sleep(0.1)
