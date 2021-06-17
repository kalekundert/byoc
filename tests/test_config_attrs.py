#!/usr/bin/env python3

import parametrize_from_file
from voluptuous import Schema
from schema_helpers import *

@parametrize_from_file(
        schema=Schema({
            'obj': exec_obj,
            'expected': {str: eval},
        })
)
def test_config_attr(obj, expected):
    for attr, value in expected.items():
        assert getattr(obj, attr) == value

@parametrize_from_file(
        schema=Schema({
            'obj': exec_obj,
            'attr': str,
            'error': error,
        })
)
def test_config_attr_err(obj, attr, error):
    with error:
        getattr(obj, attr)
