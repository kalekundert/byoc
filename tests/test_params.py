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
            Optional('locals', default=''): str,
            **error_or(
                expected=str,
            ),
            str: str,
        })
)
def test_make_map(locals, configs, values, expected, error):

    if locals:
        shared = dict(appcli=appcli)
        exec(locals, {}, shared)
    else:
        class A(appcli.Config): pass
        class B(appcli.Config): pass
        shared = dict(appcli=appcli, A=A, B=B, a=A(), b=B())

    configs = eval(configs, {}, shared)
    values = eval(values, {}, shared)
    expected = eval(expected or 'None', shared)

    with error:
        assert appcli.params.make_map(configs, values) == expected
