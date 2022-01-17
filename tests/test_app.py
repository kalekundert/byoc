#!/usr/bin/env python3

import byoc

def test_app():

    class DummyConfig(byoc.Config):
        def load(self):
            yield byoc.DictLayer(values={'x': 1}, location='a')

    class DummyObj(byoc.App):
        __config__ = [DummyConfig]
        x = byoc.param()

        def __bareinit__(self):
            self.y = 0

        def __init__(self, x):
            self.x = x

    obj = DummyObj(2)
    assert obj.x == 2
    assert obj.y == 0

    obj = DummyObj.from_bare()
    assert obj.x == 1
    assert obj.y == 0



