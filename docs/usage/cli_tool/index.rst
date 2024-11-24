=================
Command Line Tool
=================

.. toctree::
   :maxdepth: 2

The BlinkStick Command Line Tool is a simple utility that allows you to control BlinkStick devices from the command line.

Set random color for all BlinkSticks
------------------------------------

.. code-block:: bash

    blinkstick random

Set color with hex code
-----------------------

.. code-block:: bash

    blinkstick --hex 00FF00

Set blue color for the BlinkStick with serial number BS000001-1.0
-----------------------------------------------------------------

.. code-block:: bash

    blinkstick --serial BS000001-1.0 blue

Blink red color twice
---------------------

.. code-block:: bash

    blinkstick  --repeats 2 --blink red

Pulse green color three times
-----------------------------

.. code-block:: bash

    blinkstick --repeats 3 --pulse green

Morph to red, green and blue
----------------------------

.. code-block:: bash

    blinkstick --morph red
    blinkstick --morph green
    blinkstick --morph blue

Control individual pixels on BlinkStick Pro
-------------------------------------------

First you will need to set `BlinkStick Pro mode <http://www.blinkstick.com/help/tutorials/blinkstick-pro-modes>`_ to WS2812

.. code-block:: bash

    blinkstick --set-mode 2

Now you can set color of individual LEDs connected to R, G or B channels.

.. code-block:: bash

    blinkstick --channel 0 --index 5 red
