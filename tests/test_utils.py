#!/usr/bin/env python3

import appcli
import pytest
import parametrize_from_file
from schema_helpers import *
from schema import Use, Optional

@parametrize_from_file(
        schema={
            'args': Use(eval),
            Optional('kwargs', default=dict): {str: Use(eval)},
            'expected': Use(eval),
        }
)
def test_first_specified(args, kwargs, expected):
    assert appcli.utils.first_specified(*args, **kwargs) == expected

@parametrize_from_file(
        schema={
            'args': Use(eval),
            Optional('kwargs', default=dict): {str: Use(eval)},
        }
)
def test_first_specified_err(args, kwargs):
    with pytest.raises(appcli.ScriptError) as err:
        appcli.utils.first_specified(*args, **kwargs)

    assert err.match(no_templates)

@parametrize_from_file(
        schema={
            'x': Use(eval),
            'key': str,
            'expected': Use(eval),
        }
)
def test_lookup(x, key, expected):
    assert appcli.utils.lookup(x, key) == expected
