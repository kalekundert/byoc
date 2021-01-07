#!/usr/bin/env python3

import appcli
import pytest
import parametrize_from_file
from voluptuous import Schema, Optional, Or
from schema_helpers import *

@parametrize_from_file(
        schema=Schema({
            'obj': exec_obj,
            'expected': {str: eval},
        })
)
def test_param(obj, expected):
    for attr, value in expected.items():
        print(attr, value)
        assert getattr(obj, attr) == value

def test_param_init_err():
    with pytest.raises(appcli.ScriptError) as err:
        appcli.param('x', key='y')

    assert err.match(r"can't specify keys twice")
    assert err.match(r"first specification:  'x'")
    assert err.match(r"second specification: 'y'")


@parametrize_from_file(
        schema=Schema({
            'given': eval_appcli,
            'expected': eval,
        })
)
def test_is_key_list(given, expected):
    assert appcli.params._is_key_list(given) == expected

@parametrize_from_file(
        schema=Schema({
            Optional('locals', default=''): str,
            'configs': str,
            'keys': Or([str], empty_list),
            **error_or(
                expected=str,
            ),
        })
)
def test_key_map_from_key_list(locals, configs, keys, expected, error):
    shared = locals_or_ab(locals)
    configs = eval(configs, {}, shared)
    keys = [eval(x, {}, shared) for x in keys]
    expected = eval(expected or 'None', shared)

    with error:
        map = appcli.params._key_map_from_key_list(configs, keys)
        assert wrap_key_map(map, 0) == expected

@parametrize_from_file(
        schema=Schema({
            Optional('locals', default=''): str,
            **error_or(
                expected=str,
            ),
            str: str,
        })
)
def test_key_map_from_dict_equivs(locals, configs, keys, casts, expected, error):
    shared = locals_or_ab(locals)
    configs = eval(configs, {}, shared)
    keys = eval(keys, {}, shared)
    casts = eval(casts, {}, shared)
    expected = eval(expected or 'None', shared)

    with error:
        map = appcli.params._key_map_from_dict_equivs(configs, keys, casts)
        assert wrap_key_map(map, 0) == expected

@parametrize_from_file(
        schema=Schema({
            Optional('locals', default=''): str,
            **error_or(
                expected=str,
            ),
            str: str,
        })
)
def test_dict_from_equiv(locals, configs, values, expected, error):
    shared = locals_or_ab(locals)
    configs = eval(configs, {}, shared)
    values = eval(values, {}, shared)
    expected = eval(expected or 'None', shared)

    with error:
        assert appcli.params._dict_from_equiv(configs, values) == expected


def locals_or_ab(locals):
    if locals:
        shared = dict(appcli=appcli)
        exec(locals, {}, shared)
        return shared

    else:
        class A(appcli.Config): pass
        class B(appcli.Config): pass
        return dict(appcli=appcli, A=A, B=B, a=A(), b=B())

def wrap_key_map(map, x):
    return {
            cls: [
                (key, cast(x))
                for key, cast in keys_casts
            ]
            for cls, keys_casts in map.items()
    }
