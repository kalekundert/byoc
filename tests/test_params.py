#!/usr/bin/env python3

import appcli
import pytest
import parametrize_from_file
from schema import Use, Optional, Or
from schema_helpers import *

@parametrize_from_file(
        schema={
            'obj': Use(exec_obj),
            'expected': {str: Use(eval)},
        }
)
def test_param(obj, expected):
    for attr, value in expected.items():
        assert getattr(obj, attr) == value

def test_param_init_err():
    with pytest.raises(appcli.ScriptError) as err:
        appcli.param('x', key='y')

    assert err.match(r"can't specify keys twice")
    assert err.match(r"first specification:  'x'")
    assert err.match(r"second specification: 'y'")

@parametrize_from_file(
        schema={
            'configs': Or([Use(exec_config)], empty_list),
            'key_map': Or({str: Use(eval)}, empty_dict),
            'cast_map': Or({str: Use(eval)}, empty_dict),
            Optional('default', default=None): Use(eval),
            **error_or(
                expected=Or([Use(eval)], empty_list),
            ),
        }
)
def test_iter_values_from_layers(configs, key_map, cast_map, default, expected, error):
    class Obj:
        __config__ = configs

    obj = Obj()
    appcli.init(obj)
    layers = appcli.model.get_layers(obj)
    kwargs = {} if default is None else dict(default=default)

    with error:
        values = appcli.params.iter_values_from_layers(
                layers, key_map, cast_map, **kwargs)
        assert list(values) == expected

@parametrize_from_file(
        schema={
            Optional('default', default=None): Use(eval),
            str: Use(eval),
        }
)
def test_make_map(keys, values, default, expected):
    kwargs = {} if default is None else dict(default=default)
    assert appcli.params.make_map(keys, values, **kwargs) == expected