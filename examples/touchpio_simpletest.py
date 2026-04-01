# SPDX-FileCopyrightText: Copyright (c) 2023 Tod Kurt
#
# SPDX-License-Identifier: Unlicense
"""
touchpio_simpletest.py

touchpio test with a single pad. It works just like touchio.
"""

import board

import touchpio

touch = touchpio.TouchIn(board.GP2)
while True:
    if touch.value:
        print("touched!")
