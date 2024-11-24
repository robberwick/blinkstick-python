Find by Serial
==============

This example demonstrates how to find a BlinkStick device by its serial number.

.. code-block:: python

    from blinkstick import blinkstick

    bstick = blinkstick.find_by_serial("BS000001-1.0")

    if bstick is None:
        print "Not found..."
    else:
        print "BlinkStick found. Current color: " + bstick.get_color(color_format="hex")
