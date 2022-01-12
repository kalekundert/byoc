#!/usr/bin/env python3

import appcli
import pytest
import parametrize_from_file
from voluptuous import Schema, Optional
from param_helpers import *

@parametrize_from_file(
        schema=Schema({
            'args': with_py.eval,
            Optional('kwargs', default=dict): {str: with_py.eval},
            'expected': with_py.eval,
        })
)
def test_first_specified(args, kwargs, expected):
    assert appcli.utils.first_specified(*args, **kwargs) == expected

@parametrize_from_file(
        schema=Schema({
            'args': with_py.eval,
            Optional('kwargs', default=dict): {str: with_py.eval},
        })
)
def test_first_specified_err(args, kwargs):
    with pytest.raises(appcli.ApiError) as err:
        appcli.utils.first_specified(*args, **kwargs)

    assert err.match(no_templates)

@parametrize_from_file(
        schema=Schema({
            'x': with_py.eval,
            'key': with_py.eval,
            'expected': with_py.eval,
        })
)
def test_lookup(x, key, expected):
    assert appcli.utils.lookup(x, key) == expected
