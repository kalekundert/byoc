#!/usr/bin/env python3

from .errors import *
from collections.abc import Iterable

def noop(x):
    return x

def first_specified(*values, **kwargs):
    unspecified = kwargs.get('sentinel', None)

    for x in values:
        if x is not unspecified:
            return x

    try:
        return kwargs['default']
    except KeyError:
        err = ApiError(
                values=values,
                sentinel=unspecified,
        )
        err.brief = "must specify a value"
        err.blame += lambda e: f"given {len(e['values'])} {e.sentinel} values"
        err.hints += "did you mean to specify a default value?"
        raise err from None

def lookup(obj, key):
    """
    Lookup the given key in the given object.

    Arguments:
        obj: Any object.
        key:
            If callable: The callable will be called with the given object as 
            its only argument.  Whatever it returns will be taken as the value 
            of the key.

            If non-string iterable: The iterable will be considered as a 
            sequence of keys to iteratively lookup in the object.  In other 
            words, the return value will be something like 
            ``obj[key[0]][key[1]]...``.

            If anything else: The key will be looked up in the given object 
            like so: ``obj[key]``.
    """
    if callable(key):
        return key(obj)

    if isinstance(key, Iterable) and not isinstance(key, str):
        for subkey in key:
            obj = obj[subkey]
        return obj

    return obj[key]

