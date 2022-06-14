#!/usr/bin/env python3

import pytest, byoc
import parametrize_from_file

from byoc.errors import Log
from byoc.configs.layers import repr_dict_short
from param_helpers import *

values = [
        {'x': 1},
        lambda: {'x': 1},
]
locations = [
        'a',
        lambda: 'a',
]

def test_dict_layer_repr():
    layer = byoc.DictLayer(values={'x': 1}, location='a')
    assert repr(layer) == "DictLayer({'x': 1}, location='a')"

@pytest.mark.parametrize('values', values)
@pytest.mark.parametrize('location', locations)
def test_dict_layer_init(values, location):
    layer = byoc.DictLayer(values=values, location=location)
    assert layer.values == {'x': 1}
    assert layer.location == 'a'

@pytest.mark.parametrize('values', values)
@pytest.mark.parametrize('location', locations)
def test_dict_layer_setters(values, location):
    layer = byoc.DictLayer(values={}, location='')

    layer.values = values
    layer.location = location

    assert layer.values == {'x': 1}
    assert layer.location == 'a'

@parametrize_from_file(
        schema=cast(
            layer=with_byoc.eval(defer=True),
            key=with_py.eval,
            expected=with_py.eval,
        ),
)
def test_layer_iter_values(layer, key, expected, log, monkeypatch):
    monkeypatch.setenv('BYOC_VERBOSE', '1')

    layer = layer()
    actual_log = Log()
    assert list(layer.iter_values(key, actual_log)) == expected
    assert actual_log.message_strs == log

@parametrize_from_file(
        schema=[
            cast(dict=with_py.eval, n_max=int),
            defaults(env={}),
        ],
)
def test_repr_dict_short(dict, env, expected, monkeypatch):
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    assert repr_dict_short(dict) == expected

