#!/usr/bin/env python3

import pytest, appcli
import parametrize_from_file
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
    layer = appcli.DictLayer(values={'x': 1}, location='a')
    assert repr(layer) == "DictLayer({'x': 1}, location='a')"

@pytest.mark.parametrize('values', values)
@pytest.mark.parametrize('location', locations)
def test_dict_layer_init(values, location):
    layer = appcli.DictLayer(values=values, location=location)
    assert layer.values == {'x': 1}
    assert layer.location == 'a'

@pytest.mark.parametrize('values', values)
@pytest.mark.parametrize('location', locations)
def test_dict_layer_setters(values, location):
    layer = appcli.DictLayer(values={}, location='')

    layer.values = values
    layer.location = location

    assert layer.values == {'x': 1}
    assert layer.location == 'a'

@parametrize_from_file(
        schema=Schema({
            'layer': with_appcli.eval,
            'expected': {str: with_appcli.eval},
        }),
)
def test_dict_layer_iter_values(layer, expected):
    for key in expected:
        assert list(layer.iter_values(key, Mock())) == expected[key]

