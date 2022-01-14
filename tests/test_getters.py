#!/usr/bin/env python3

import pytest, re
import parametrize_from_file

from byoc.errors import Log
from re_assert import Matches
from more_itertools import zip_equal, unzip
from param_helpers import *

@parametrize_from_file(
        schema=Schema({
            'getter': with_byoc.eval,
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
            Optional('attr', default='byoc.attr()'): str,
            'getter': str,
            'given': with_py.eval,
            **with_byoc.error_or({
                'expected': with_py.eval,
            }),
        }),
)
def test_getter_cast_value(obj, attr, getter, given, expected, error):
    with_obj = with_byoc.exec(obj)
    obj = get_obj(with_obj)
    attr = with_obj.eval(attr)
    getter = with_obj.eval(getter)

    # Pretend to initialize the descriptor.
    if not hasattr(attr, '_name'):
        attr.__set_name__(obj.__class__, '')

    byoc.init(obj)
    bound_getter = getter.bind(obj, attr)

    with error:
        assert bound_getter.cast_value(given) == expected

@parametrize_from_file(
        schema=Schema({
            Optional('obj', default='class DummyObj: __config__ = []'): str,
            Optional('attr', default=''): str,
            'getter': str,
            **with_byoc.error_or({
                'expected': {
                    'values': with_py.eval,
                    'meta': empty_ok([eval_meta]),
                    'dynamic': empty_ok([with_py.eval]),
                    'log': [str],
                },
            }),
        }),
)
def test_getter_iter_values(getter, obj, attr, expected, error):
    with_obj = with_byoc.exec(obj)
    obj = get_obj(with_obj)
    attr = find_attr(obj, attr)
    getter = with_obj.eval(getter)

    byoc.init(obj)
    bound_getter = getter.bind(obj, attr)
    log = Log()

    with error:
        iter = bound_getter.iter_values(log)

        # Can simplify this after more_itertools#591 is resolved.
        try:
            values, metas, dynamic = unzip(iter)
        except ValueError:
            values, metas, dynamic = [], [], []
        
        assert list(values) == expected['values']
        assert list(metas) == expected['meta']
        assert list(dynamic) == expected['dynamic']

        for log_str, pattern in zip_equal(log._err.info_strs, expected['log']):
            Matches(pattern).assert_matches(log_str)

@parametrize_from_file(
        schema=Schema({
            Optional('obj', default='class DummyObj: __config__ = []'): str,
            Optional('attr', default=''): str,
            'getter': str,
            'error': with_byoc.error,
        }),
)
def test_getter_kwargs_err(obj, attr, getter, error):
    with_obj = with_byoc.exec(obj)
    obj = get_obj(with_obj)
    attr = find_attr(obj, attr)
    getter = with_obj.eval(getter)

    byoc.init(obj)

    with error:
        getter.bind(obj, attr)

