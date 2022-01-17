#!/usr/bin/env python3

import byoc
from byoc import Config, DictLayer

class DictConfig(Config):

    def load(self):
        yield DictLayer(values=self.values)

class DictConfigAB(DictConfig):
    values = {'a': 1, 'b': 1}

class DictConfigAC(DictConfig):
    values = {'a': 2, 'c': 2}


def test_easy_1():

    class DummyObj:
        __config__ = [DictConfigAB]
        a = byoc.param()

    obj = DummyObj()
    assert obj.a == 1

def test_easy_2():

    class DummyObj:
        __config__ = [
                DictConfigAB,
                DictConfigAC,
        ]
        a = byoc.param()
        b = byoc.param()
        c = byoc.param()

    obj = DummyObj()
    assert obj.a == 1
    assert obj.b == 1
    assert obj.c == 2
