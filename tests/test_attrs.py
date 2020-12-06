#!/usr/bin/env python3

import parametrize_from_file
from schema import Use
from schema_helpers import *

@parametrize_from_file(
        schema={
            'obj': Use(exec_obj),
            'expected': {str: Use(eval)},
        }
)
def test_attr(obj, expected):
    for attr, value in expected.items():
        assert getattr(obj, attr) == value

@parametrize_from_file(
        schema={
            'obj': Use(exec_obj),
            'attr': str,
            'error': Use(error),
        }
)
def test_attr_err(obj, attr, error):
    with error:
        getattr(obj, attr)
