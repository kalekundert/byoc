#!/usr/bin/env python3

import pytest, re
import parametrize_from_file
import byoc

from byoc.errors import Log
from more_itertools import one, zip_equal, unzip, padded, last
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
                param=None,
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
    # This test is meant for cases where we're interested in more than just the 
    # value that ultimately gets calculated, i.e. we're interested *metadata*, 
    # *dynamic*, or *log*.  If we only care about the value, the `test_param` 
    # test (in `test_params.py`) will be simpler and more realistic.

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
        
        bound_getter.cleanup(log)

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

@parametrize_from_file(schema=cast(expected=with_py.eval))
def test_part(funcs, obj, expected, n_calls):

    # Wrap all the probe function in mock objects, so that we can keep track of 
    # how many times they're called:
    with_funcs = {}
    for func_name, func_str in funcs.items():
        f = with_py.eval(func_str)
        with_funcs[func_name] = Mock(side_effect=f)

    # Normalize the structure of the dictionary containing the expected call 
    # counts:
    last_attr = last(expected)
    for f, n in n_calls.items():
        if isinstance(n, str):
            n_calls[f] = {last_attr: int(n)}
        else:
            n_calls[f] = {k: int(v) for k, v in n_calls[f].items()}

    # Perform the test:
    obj = with_byoc.fork(with_funcs).exec(obj, get=get_obj)

    for attr, value in expected.items():
        assert getattr(obj, attr) == value

        for f, n in n_calls.items():
            if attr in n:
                assert with_funcs[f].call_count == n[attr], (f, attr)
