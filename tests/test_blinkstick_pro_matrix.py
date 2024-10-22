from blinkstick.blinkstick import BlinkStickPro


def test_instantiate():
    bs = BlinkStickPro()
    assert bs is not None
