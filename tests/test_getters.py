#!/usr/bin/env python3

import pytest, re
import parametrize_from_file

from appcli.model import get_configs
from schema_helpers import *

@parametrize_from_file(
        schema=Schema({
            'getter': eval_appcli,
            'expected': str,
        }),
)
def test_getter_repr(getter, expected):
    print(repr(getter))
    print(expected)
    assert re.fullmatch(expected, repr(getter))

@parametrize_from_file(
        schema=Schema({
            Optional('obj', default='class DummyObj:\n __config__ = []'): str,
            Optional('param', default='appcli.param()'): str,
            'getter': str,
            'given': eval,
            **error_or(**{
                'expected': eval,
            }),
        }),
)
def test_getter_cast_value(obj, param, getter, given, expected, error):
    globals = {}
    obj = exec_obj(obj, globals)
    param = eval_appcli(param, globals)
    getter = eval_appcli(getter, globals)

    # Pretend to initialize the descriptor.
    if not hasattr(param, '_name'):
        param.__set_name__(obj.__class__, '')

    appcli.init(obj)
    bound_getter = getter.bind(obj, param)

    with error:
        assert bound_getter.cast_value(given) == expected

@parametrize_from_file(
        schema=Schema({
            Optional('obj', default='class DummyObj: __config__ = []'): str,
            Optional('param', default=''): str,
            'getter': str,
            'expected': {
                'values': eval,
                'configs': eval,
                Optional('locations'): eval,
            },
        }),
)
def test_getter_iter_values(getter, obj, param, expected):
    globals = {}
    obj = exec_obj(obj, globals)
    param = find_param(obj, param)
    getter = eval_appcli(getter, globals)

    appcli.init(obj)
    bound_getter = getter.bind(obj, param)

    configs, locations = [], []
    values = bound_getter.iter_values(configs, locations)

    assert list(values) == expected['values']
    assert configs == [get_configs(obj)[i] for i in expected['configs']]
    assert [tuple(map(str, x)) for x in locations] == expected['locations']

@parametrize_from_file(
        schema=Schema({
            Optional('obj', default='class DummyObj: __config__ = []'): str,
            Optional('param', default=''): str,
            'getter': str,
            'error': error,
        }),
)
def test_getter_kwargs_err(obj, param, getter, error):
    globals = {}
    obj = exec_obj(obj, globals)
    param = find_param(obj, param)
    getter = eval_appcli(getter, globals)

    appcli.init(obj)

    with error:
        getter.bind(obj, param)

