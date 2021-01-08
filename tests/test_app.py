#!/usr/bin/env python3

import appcli

def test_app():

    class DummyConfig(appcli.Config):
        def load(self, obj):
            yield appcli.Layer(values={'x': 1}, location='a')

    class DummyObj(appcli.App):
        __config__ = [DummyConfig()]
        x = appcli.param()

        def __bareinit__(self):
            self.y = 0

        def __init__(self, x):
            self.x = x

    obj = DummyObj(2)
    assert obj.x == 2
    assert obj.y == 0

    obj = DummyObj.from_params()
    assert obj.x == 1
    assert obj.y == 0



