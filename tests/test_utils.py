#!/usr/bin/env python3

import byoc
import pytest
import parametrize_from_file

from byoc.utils import *
from param_helpers import *

@parametrize_from_file(
        schema=[
            with_py.eval,
            defaults(kwargs={}),
        ],
)
def test_first_specified(args, kwargs, expected):
    assert byoc.utils.first_specified(*args, **kwargs) == expected

@parametrize_from_file(
        schema=[
            with_py.eval,
            defaults(kwargs={}),
        ],
)
def test_first_specified_err(args, kwargs):
    with pytest.raises(byoc.ApiError) as err:
        byoc.utils.first_specified(*args, **kwargs)

    assert err.match(no_templates)

@parametrize_from_file(schema=with_py.eval)
def test_lookup(x, key, expected):
    assert byoc.utils.lookup(x, key) == expected

def test_replay_11_22():
    it = iter([1, 2])

    r = replay(it)
    r1, r2 = iter(r), iter(r)

    assert next(r1) == (1, True)
    assert next(r1) == (2, True)
    with pytest.raises(StopIteration): next(r1)

    assert next(r2) == (1, False)
    assert next(r2) == (2, False)
    with pytest.raises(StopIteration): next(r2)

def test_replay_12_12():
    it = iter([1, 2])

    r = replay(it)
    r1, r2 = iter(r), iter(r)

    assert next(r1) == (1, True)
    assert next(r2) == (1, False)

    assert next(r1) == (2, True)
    assert next(r2) == (2, False)

    with pytest.raises(StopIteration): next(r1)
    with pytest.raises(StopIteration): next(r2)

def test_replay_12_21():
    it = iter([1, 2])

    r = replay(it)
    r1, r2 = iter(r), iter(r)

    assert next(r1) == (1, True)
    assert next(r2) == (1, False)

    assert next(r2) == (2, True)
    assert next(r1) == (2, False)

    with pytest.raises(StopIteration): next(r1)
    with pytest.raises(StopIteration): next(r2)

