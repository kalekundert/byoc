#!/usr/bin/env python3

from .errors import *

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
        err = ScriptError(
                values=values,
                sentinel=unspecified,
        )
        err.brief = "must specify a value"
        err.blame += lambda e: f"given {len(e['values'])} {e.sentinel} values"
        err.hints += "did you mean to specify a default value?"
        raise err from None

def lookup(x, key, sep='.'):
    if callable(key):
        return key(x)

    for subkey in key.split(sep):
        x = x(subkey) if callable(x) else x[subkey]
    return x
