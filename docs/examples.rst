Simple test
------------

Ensure your device works with this simple test.

.. literalinclude:: ../examples/touchpio_simpletest.py
    :caption: examples/touchpio_simpletest.py
    :linenos:

TouchInMulti simple test
-------------------------

Demo of ``TouchInMulti`` with 16 pads, calibration, and a bar-graph display of active pads.

.. literalinclude:: ../examples/touchpio_mulit_simpletest.py
    :caption: examples/touchpio_mulit_simpletest.py
    :linenos:

TouchIn many pins
------------------

Demo of 8 individual ``TouchIn`` instances. Note this exhausts all PIO state machines;
for single-pin use, ``touchio`` is preferred.

.. literalinclude:: ../examples/touchpio_touchin_many.py
    :caption: examples/touchpio_touchin_many.py
    :linenos:
