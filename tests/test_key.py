#!/usr/bin/env python3

import byoc
from byoc import Key, Config, DictLayer, jmes

def test_jmes():

    class DummyConfig(Config):
        def load(self):
            yield DictLayer({'x': {'y': 1}})

    class DummyObj:
        __config__ = [DummyConfig]
        x = byoc.param(
                Key(DummyConfig, jmes('x.y')),
        )

    obj = DummyObj()
    assert obj.x == 1

