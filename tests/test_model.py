#!/usr/bin/env python3

import pytest
import parametrize_from_file
import appcli
from voluptuous import Schema, Or, Optional, Coerce
from schema_helpers import *
from more_itertools import zip_equal

class DummyObj:
    pass

class DummyConfig(appcli.Config):

    def __init__(self, layers):
        self.layers = layers

    def load(self, obj):
        return layers

@parametrize_from_file(
        schema=Schema({
            'obj': exec_obj,
            'init_layers': Or([str], empty_list),
            'load_layers': Or([str], empty_list),
        })
)
def test_init_load(obj, init_layers, load_layers):
    locals = dict(
            configs=appcli.model.get_configs(obj),
    )

    appcli.init(obj)
    assert appcli.model.get_layers(obj) == eval_layers(init_layers, **locals)

    try:
        obj.load()
    except AttributeError:
        appcli.load(obj)

    assert appcli.model.get_layers(obj) == eval_layers(load_layers, **locals)

def test_get_configs():

    sentinel = object()
    class Obj:
        __config__ = sentinel

    obj = Obj()
    assert appcli.model.get_configs(obj) is sentinel

def test_get_configs_err():
    obj = DummyObj()

    with pytest.raises(appcli.ScriptError) as err:
        appcli.model.get_configs(obj)

    assert err.match('object not configured for use with appcli')
    assert err.match(no_templates)

@parametrize_from_file(
        schema=Schema({
            'config': exec_config,
            'expected': Or([eval], empty_list),
        })
)
def test_load_config(config, expected):
    obj = DummyObj()
    layers = appcli.model.load_config(config, obj)

    expected = [
            (config, value, loc)
            for value, loc in expected
    ]
    actual = [
            (x.config, x.values, x.location)
            for x in layers
    ]
    assert actual == expected

@parametrize_from_file(
        schema=Schema({
            'layers':   Or([eval_appcli], empty_list),
            'expected': Or([eval_appcli], empty_list),
        })
)
def test_iter_active_layers(layers, expected):

    class Obj:
        __config__ = []

    obj = Obj()
    appcli.init(obj)
    appcli.model.get_meta(obj).layers = layers

    expected = [LayerWrapper(x) for x in expected]
    assert list(appcli.model.iter_active_layers(obj)) == expected

@parametrize_from_file(
        schema=Schema({
            'obj': exec_obj,
            'key_map': Or({Coerce(int): eval}, empty_dict),
            'cast_map': Or({Coerce(int): eval}, empty_dict),
            Optional('default', default=None): Or(None, eval),
            **error_or(
                expected=Or([eval], empty_list),
            ),
        })
)
def test_iter_values(obj, key_map, cast_map, default, expected, error):
    configs = appcli.model.get_configs(obj)
    key_map = {configs[i]: v for i, v in key_map.items()}
    cast_map = {configs[i]: v for i, v in cast_map.items()}
    kwargs = {} if default is None else dict(default=default)

    with error:
        values = appcli.model.iter_values(
                obj, key_map, cast_map, **kwargs)
        assert list(values) == expected


