#!/usr/bin/env python3

import appcli
import pytest
import parametrize_from_file
from voluptuous import Schema, Optional
from schema_helpers import *

@parametrize_from_file(
        schema=Schema({
            'args': eval,
            Optional('kwargs', default=dict): {str: eval},
            'expected': eval,
        })
)
def test_first_specified(args, kwargs, expected):
    assert appcli.utils.first_specified(*args, **kwargs) == expected

@parametrize_from_file(
        schema=Schema({
            'args': eval,
            Optional('kwargs', default=dict): {str: eval},
        })
)
def test_first_specified_err(args, kwargs):
    with pytest.raises(appcli.ScriptError) as err:
        appcli.utils.first_specified(*args, **kwargs)

    assert err.match(no_templates)

@parametrize_from_file(
        schema=Schema({
            'x': eval,
            'key': eval,
            'expected': eval,
        })
)
def test_lookup(x, key, expected):
    assert appcli.utils.lookup(x, key) == expected
