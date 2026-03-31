# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Tod Kurt
#
# SPDX-License-Identifier: Unlicense

import board

import touchpio

touch = touchpio.TouchIn(board.GP2)
while True:
    if touch.value:
        print("touched!")
