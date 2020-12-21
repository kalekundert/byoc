#!/usr/bin/env python3

from appcli import param, DefaultConfig

def test_easy():

    class Foo:
        __config__ = [
                DefaultConfig(a=1),
        ]

        a = param()

    f = Foo()
    assert f.a == 1


def test_easy_2():
    class Foo:
        __config__ = [
                DefaultConfig(a=1, b=1,    ),
                DefaultConfig(a=2,      c=2),
        ]

        a = param()
        b = param()
        c = param()

    f = Foo()
    assert f.a == 1
    assert f.b == 1
    assert f.c == 2
