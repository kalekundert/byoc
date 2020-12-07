#!/usr/bin/env python3

import pytest
import parametrize_from_file
import appcli
from voluptuous import Schema, Or, Optional
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
            Optional('obj', default=DummyObj): Or(DummyObj, exec_obj),
            'configs': Or({str: exec_config}, empty_dict),
            'init_layers': Or([str], empty_list),
            'load_layers': Or([eval_appcli], empty_list),
        })
)
def test_init_load(obj, configs, init_layers, load_layers):
    # `configs` is a dictionary, but the values are guaranteed to be in the 
    # order the appear in the parameter file.
    obj.__config__ = list(configs.values())

    appcli.init(obj)
    assert appcli.model.get_layers(obj) == [
            LayerWrapper(eval_appcli(x, **configs))
            for x in init_layers
    ]

    appcli.load(obj)
    assert appcli.model.get_layers(obj) == [
            LayerWrapper(x)
            for x in load_layers
    ]

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
            'config': exec_config,
            'error': str,
        })
)
def test_load_config_err(config, error):
    obj = DummyObj()
    with pytest.raises(appcli.ScriptError) as err:
        appcli.model.load_config(config, obj)

    assert err.match(error)
    assert err.match(no_templates)

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
        key='test_groups',
        schema=Schema({
            'groups': Or(list, empty_list),
            'expected': Or(list, empty_list),
        })
)
def test_get_key_groups(groups, expected):

    class Obj:
        __config__ = [appcli.Config(key_group=x) for x in groups]

    obj = Obj()
    assert appcli.model.get_key_groups(obj) == expected

@parametrize_from_file(
        key='test_groups',
        schema=Schema({
            'groups': Or(list, empty_list),
            'expected': Or(list, empty_list),
        })
)
def test_get_cast_groups(groups, expected):

    class Obj:
        __config__ = [appcli.Config(cast_group=x) for x in groups]

    obj = Obj()
    assert appcli.model.get_cast_groups(obj) == expected

