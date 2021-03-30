#!/usr/bin/env python3

import pytest
import appcli

values = [
        {'x': 1},
        lambda: {'x': 1},
]
locations = [
        'a',
        lambda: 'a',
]

@pytest.mark.parametrize('values', values)
@pytest.mark.parametrize('location', locations)
def test_layer_init(values, location):
    layer = appcli.Layer(values=values, location=location)
    assert layer.values == {'x': 1}
    assert layer.location == 'a'

@pytest.mark.parametrize('values', values)
@pytest.mark.parametrize('location', locations)
def test_layer_setters(values, location):
    layer = appcli.Layer(values={}, location='')

    layer.values = values
    layer.location = location

    assert layer.values == {'x': 1}
    assert layer.location == 'a'

def test_layer_repr():
    layer = appcli.Layer(values={'x': 1}, location='a')
    assert repr(layer) == "Layer(values={'x': 1}, location='a')"


