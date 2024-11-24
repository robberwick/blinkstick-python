Access InfoBlocks
=================

Infoblocks are basic data that can be stored on the device. Each infoblock consists of 32 bytes. Infoblock1 is used to store the name of the BlinkStick.



.. code-block:: python

    from blinkstick import blinkstick

    bstick = blinkstick.find_first()

    # set and get device info-block1 here
    bstick.set_info_block1("Kitchen BlinkStick")
    print (bstick.get_info_block1())

    # set and get device info-block2 here
    bstick.set_info_block2("info-block-2data")
    print (bstick.get_info_block2())
