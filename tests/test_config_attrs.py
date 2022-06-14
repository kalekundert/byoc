#!/usr/bin/env python3

import parametrize_from_file
from param_helpers import *

@parametrize_from_file(
        schema=cast(
            obj=with_byoc.exec(get=get_obj, defer=True),
            expected=with_py.eval,
        ),
)
def test_config_attr(obj, expected):
    obj = obj()
    for attr, value in expected.items():
        assert getattr(obj, attr) == value

@parametrize_from_file(
        schema=cast(
            obj=with_byoc.exec(get=get_obj, defer=True),
            error=with_byoc.error,
        ),
)
def test_config_attr_err(obj, attr, error):
    obj = obj()
    with error:
        getattr(obj, attr)
