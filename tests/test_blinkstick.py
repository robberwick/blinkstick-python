from blinkstick.blinkstick import BlinkStick


def test_instantiate():
    bs = BlinkStick()
    assert bs is not None
