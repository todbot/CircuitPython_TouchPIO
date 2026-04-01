# SPDX-FileCopyrightText: Copyright (c) 2026 Tod Kurt
#
# SPDX-License-Identifier: Unlicense

"""
touchpio_multi_simpletest.py — Demo of touchpio_multi on a Raspberry Pi Pico

Wiring:
  GPIO 0–15  → touch pads (copper tape, PCB pads, etc.)
  Each pad  → 1MΩ resistor → GND
"""

import time

import board

import touchpio

touch = touchpio.TouchInMulti(
    first_pin=board.GP0,
    num_pins=16,
    # num_samples     = 250,
    touch_threshold=20,
    # thresholds      = range(0, 5001, 100),
    # thresholds      = range(0, 5001, 50),
    # thresholds      = range(0, 2000, 100),
    # thresholds      = range(100, 2001, 50),   # 40 levels
    # thresholds      = range(100, 2001, 100),   # 20 levels
    # touch_threshold = 1,                        # levels above baseline
)

print(f"Pull type: {touch.pull_type}")
print("Calibrating — don't touch the pads...")
time.sleep(1.0)
touch.calibrate(num_samples=20)
print("Baseline:", touch.baseline)
print()

print("Ready — touch the pads!")
while True:
    values = touch.read()
    active = touch.touched_pins()

    if active:
        bar = " ".join(f"[P{i}:{'█' * min(values[i], 15)}]" for i in active)
        print(bar)

    time.sleep(0.03)
