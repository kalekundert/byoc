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
            'init_layers': Or(eval_layers, empty_list),
            'load_layers': Or(eval_layers, empty_list),
            Optional('reload_layers', default=[]):
                Or(eval_layers, empty_list),
        })
)
def test_init_load_reload(obj, init_layers, load_layers, reload_layers):
    if not reload_layers:
        reload_layers = load_layers

    appcli.init(obj)
    assert list(appcli.model.iter_layers(obj)) == init_layers

    try:
        obj.load()
    except AttributeError:
        appcli.load(obj)

    assert list(appcli.model.iter_layers(obj)) == load_layers

    try:
        obj.reload()
    except AttributeError:
        appcli.reload(obj)

    assert list(appcli.model.iter_layers(obj)) == reload_layers

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
            'obj': exec_obj,
            'key_map': Or({Coerce(int): [eval]}, empty_dict),
            Optional('default', default=None): Or(None, eval),
            **error_or(
                expected=Or([eval], empty_list),
            ),
        })
)
def test_iter_values(obj, key_map, default, expected, error):
    configs = appcli.model.get_configs(obj)
    key_map = {configs[i]: v for i, v in key_map.items()}
    kwargs = {} if default is None else dict(default=default)

    appcli.init(obj)

    with error:
        values = appcli.model.iter_values(obj, key_map, **kwargs)
        assert list(values) == expected


