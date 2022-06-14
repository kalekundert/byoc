#!/usr/bin/env python3

import byoc
import pytest
import parametrize_from_file

from byoc.cast import call_with_context
from param_helpers import *

@parametrize_from_file(
        schema=[
            defaults(
                meta='class DummyMeta: pass',
                obj='class DummyObj: pass',
            ),
            cast(
                func=with_byoc.exec(get='f'),
                value=with_py.eval,
                meta=with_py.exec(get=get_meta),
                obj=with_py.exec(get=get_obj),
                expected=with_py.eval,
            ),
            error_or('expected'),
        ],
)
def test_call_with_context(func, value, meta, obj, expected, error):
    context = byoc.Context(value, meta, obj)
    with error:
        assert call_with_context(func, context) == expected

@parametrize_from_file(
        schema=cast(
            obj=with_byoc.exec(get=get_obj, defer=True),
            files=Schema(files.schema)
        ),
        indirect=['files'],
)
def test_relpath(obj, expected, files, monkeypatch):
    monkeypatch.chdir(files)

    obj = obj.exec()
    for param, relpath in expected.items():
        assert getattr(obj, param) == files / relpath

@parametrize_from_file(
        schema=[
            cast(expected=with_py.eval),
            error_or('expected'),
        ],
)
def test_arithmetic_eval(expr, expected, error):
    with error:
        assert byoc.arithmetic_eval(expr) == expected

    with error:
        assert byoc.int_eval(expr) == int(expected)

    with error:
        assert byoc.float_eval(expr) == float(expected)
