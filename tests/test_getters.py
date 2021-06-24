#!/usr/bin/env python3

import pytest, re
import parametrize_from_file

from appcli.model import Log
from schema_helpers import *
from re_assert import Matches
from more_itertools import zip_equal

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
            **error_or(**{
                'expected': {
                    'values': eval,
                    'info': [str],
                    Optional('hints', default=[]): [str],
                },
            }),
        }),
)
def test_getter_iter_values(getter, obj, param, expected, error):
    globals = {}
    obj = exec_obj(obj, globals)
    param = find_param(obj, param)
    getter = eval_appcli(getter, globals)

    appcli.init(obj)
    bound_getter = getter.bind(obj, param)
    log = Log()

    with error:
        values = bound_getter.iter_values(log)

        assert list(values) == expected['values']

        for info, pattern in zip_equal(log.err.info_strs, expected['info']):
            Matches(pattern).assert_matches(info)

        for hint, pattern in zip_equal(log.err.hint_strs, expected['hints']):
            Matches(pattern).assert_matches(hint)

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

