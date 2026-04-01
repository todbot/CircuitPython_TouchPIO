Introduction
============


.. image:: https://readthedocs.org/projects/circuitpython-touchpio/badge/?version=latest
    :target: https://circuitpython-touchpio.readthedocs.io/
    :alt: Documentation Status



.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://adafru.it/discord
    :alt: Discord


.. image:: https://github.com/todbot/CircuitPython_TouchPIO/workflows/Build%20CI/badge.svg
    :target: https://github.com/todbot/CircuitPython_TouchPIO/actions
    :alt: Build Status


.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Code Style: Ruff


Capacitive touch sensing using Pico / Pico2 / RP2040 / RP2350 PIO, using touchio API


Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* RP2040- or RP2350-based microcontrollers (as it uses their PIO module)


Hardware
========

Each touch pad connects to a GPIO pin with a ~1MΩ resistor to ground
(pull-down, the default) or to 3.3V (pull-up). Pads can be exposed copper,
foil tape, conductive fabric, etc.

This library only works on RP2040- or RP2350-based boards like the
Raspberry Pi Pico, QTPY RP2040, and similar.


Usage Example
=============

.. code-block:: python

    import touchpio
    import board

    touch = touchpio.TouchIn(board.GP2)
    while True:
    	if touch.value:
            print("touched!")


Installing to a Connected CircuitPython Device with Circup
==========================================================

Make sure that you have ``circup`` installed in your Python environment.
Install it with the following command if necessary:

.. code-block:: shell

    pip3 install circup

With ``circup`` installed and your CircuitPython device connected use the
following command to install:

.. code-block:: shell

    circup install touchpio

Or the following command to update an existing version:

.. code-block:: shell

    circup update


Documentation
=============
API documentation for this library can be found on `Read the Docs <https://circuitpython-touchpio.readthedocs.io/>`_.

For information on building library documentation, please check out
`this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.

References
==========

* Originally from `23 Feb 2023 picotouch_grid research
  <https://github.com/todbot/picotouch/tree/main/circuitpython/research/picotouch_grid/picotouch_grid>`_

* Uses ideas from `PIO Capsense experiment / -scottiebabe 2022
  <https://community.element14.com/products/raspberry-pi/f/forum/51242/want-to-create-a-capacitance-proximity-touch-sensor-with-a-rp2040-pico-board-using-pio/198662>`_

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/todbot/CircuitPython_TouchPIO/blob/HEAD/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.
