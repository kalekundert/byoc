#!/usr/bin/env python3

import pytest, re
import parametrize_from_file
import byoc

from byoc.errors import Log
from more_itertools import zip_equal, unzip, padded
from param_helpers import *

with_getters = Namespace(
        with_byoc,
        'from byoc.getters import ImplicitKey',
        'from byoc.model import WrappedConfig',
)

@parametrize_from_file(
        schema=cast(getter=with_getters.eval),
)
def test_getter_repr(getter, expected):
    print(repr(getter))
    print(expected)
    assert re.fullmatch(expected, repr(getter))

@parametrize_from_file(
        schema=[
            defaults(
                obj='class DummyObj: pass',
                param='byoc.param()',
                meta='class DummyMeta: pass',
            ),
            cast(
                meta=with_py.exec(get=get_meta),
                given=with_py.eval,
                expected=with_py.eval,
            ),
            with_byoc.error_or('expected'),
        ],
)
def test_getter_cast_value(obj, param, meta, getter, given, expected, error):
    with_obj = with_byoc.exec(obj)
    obj = get_obj(with_obj)
    param = with_obj.eval(param)
    getter = with_obj.eval(getter)

    # Pretend to initialize the descriptor.
    if not hasattr(param, '_name'):
        param.__set_name__(obj.__class__, '')

    byoc.init(obj)
    bound_getter = getter.bind(obj, param)

    with error:
        assert bound_getter.cast_value(given, meta) == expected

@parametrize_from_file(
        schema=[
            defaults(
                obj='class DummyObj: pass',
                param='',
            ),
            cast(
                expected=Schema({
                    'values': with_py.eval,
                    'meta': empty_ok([eval_meta]),
                    'dynamic': empty_ok([with_py.eval]),
                    'log': [str],
                }),
            ),
            error_or('expected'),
        ],
)
def test_getter_iter_values(getter, obj, param, expected, error, monkeypatch):
    monkeypatch.setenv('BYOC_VERBOSE', '1')

    with_obj = with_byoc.exec(obj)
    obj = get_obj(with_obj)
    param = find_param(obj, param)
    getter = with_obj.eval(getter)

    byoc.init(obj)
    bound_getter = getter.bind(obj, param)
    log = Log()

    with error:
        iter = bound_getter.iter_values(log)

        # Can simplify this after more_itertools#591 is resolved.
        try:
            values, metas, dynamic = padded(unzip(iter), [], 3)
        except ValueError:
            values, metas, dynamic = [], [], []
        
        assert list(values) == expected['values']
        assert list(metas) == expected['meta']
        assert list(dynamic) == expected['dynamic']

        assert_log_matches(log, expected['log'])

@parametrize_from_file(
        schema=[
            defaults(
                obj='class DummyObj: pass',
                param='',
            ),
            cast(error=with_byoc.error),
        ],
)
def test_getter_kwargs_err(obj, param, getter, error):
    with_obj = with_byoc.exec(obj)
    obj = get_obj(with_obj)
    param = find_param(obj, param)
    getter = with_obj.eval(getter)

    byoc.init(obj)

    with error:
        getter.bind(obj, param)

