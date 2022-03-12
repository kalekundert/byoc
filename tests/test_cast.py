#!/usr/bin/env python3

import byoc
import pytest
import parametrize_from_file
from param_helpers import *

@parametrize_from_file(
        schema=Schema({
            'expr': str,
            **with_py.error_or({
                'expected': with_py.eval,
            }),
        }),
)
def test_arithmetic_eval(expr, expected, error):
    with error:
        assert byoc.arithmetic_eval(expr) == expected

    with error:
        assert byoc.int_eval(expr) == int(expected)

    with error:
        assert byoc.float_eval(expr) == float(expected)
