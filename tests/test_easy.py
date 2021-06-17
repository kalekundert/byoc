#!/usr/bin/env python3

from appcli import param, Config, DictLayer

class DictConfig(Config):

    def load(self):
        yield DictLayer(values=self.values)

class DictConfigAB(DictConfig):
    values = {'a': 1, 'b': 1}

class DictConfigAC(DictConfig):
    values = {'a': 2, 'c': 2}


def test_easy_1():

    class Foo:
        __config__ = [
                DictConfigAB,
        ]

        a = param()

    f = Foo()
    assert f.a == 1

def test_easy_2():
    class Foo:
        __config__ = [
                DictConfigAB,
                DictConfigAC,
        ]

        a = param()
        b = param()
        c = param()

    f = Foo()
    assert f.a == 1
    assert f.b == 1
    assert f.c == 2
