Set Random Color
================

This example demonstrates how to set a random color for a BlinkStick device.

.. code-block:: python

    from blinkstick import blinkstick

    for bstick in blinkstick.find_all():
        bstick.set_random_color()
        print (bstick.get_serial() + " " + bstick.get_color(color_format="hex"))
