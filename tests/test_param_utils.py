#!/usr/bin/env python3

import byoc
import pytest
import parametrize_from_file
from param_helpers import *

def test_jmes():
    from byoc import Key, Config, DictLayer, jmes

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

@parametrize_from_file(
        schema=Schema({
            'expr': str,
            **with_py.error_or({
                'expected': with_py.eval,
            }),
        }),
)
def test_arithmetic_eval(expr, expected, error):
    with error:
        assert byoc.arithmetic_eval(expr) == expected

    with error:
        assert byoc.int_eval(expr) == int(expected)

    with error:
        assert byoc.float_eval(expr) == float(expected)
