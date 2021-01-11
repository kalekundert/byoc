#!/usr/bin/env python3

import appcli
import pytest
from voluptuous import Schema, And, Or, Optional, Invalid
from contextlib import contextmanager

class LayerWrapper:

    def __init__(self, layer):
        self.layer = layer

    def __repr__(self):
        return f'LayerWrapper({self.layer!r})'

    def __eq__(self, other):
        return all((
                isinstance(other, appcli.Layer),
                self.layer.values == other.values,
                self.layer.location == str(other.location),
        ))

def eval_appcli(code, **locals):
    globals = dict(appcli=appcli)
    try:
        return eval(code, globals, locals)
    except Exception as err:
        raise Invalid(str(err)) from err

def eval_layers(layers, **locals):
    schema = Schema([lambda x: eval_layer(x, **locals)])
    return schema(layers)

def eval_layer(layer, **locals):
    schema = Schema(Or(str, {
        'values': eval,
        'location': str,
    }))
    layer = schema(layer)
    layer = eval_appcli(layer, **locals) if isinstance(layer, str) else appcli.Layer(**layer)
    return LayerWrapper(layer)

def exec_appcli(code, **locals):
    globals = dict(appcli=appcli, **locals)
    try:
        exec(code, globals)
    except Exception as err:
        raise Invalid(str(err)) from err
    return globals

def exec_obj(code, **locals):
    locals = exec_appcli(code, **locals) 
    try:
        return locals['obj']
    except KeyError:
        return locals['DummyObj']()

def exec_config(code, **locals):
    locals = exec_appcli(code, **locals) 
    try:
        return locals['config']
    except KeyError:
        return locals['DummyConfig']()

empty_list = And('', lambda x: [])
empty_dict = And('', lambda x: {})
no_templates = '^[^{}]*$'

class nullcontext:
    # This context manager is built in to python>=3.7

    def __enter__(self):
        pass

    def __exit__(self, *exc):
        pass

def error_or(**expected):
    schema = {}

    # Either specify an error or an expected value, not both.
    # KBK: This doesn't work for some reason.
    #schema[Or('error', *expected, only_one=True)] = object

    schema[Optional('error', default='none')] = error

    schema.update({
        Optional(k, default=None): Or(None, v)
        for k, v in expected.items()
    })
    return schema

# Something to think about: I'd like to put a version of this function in the 
# `parametrize_from_file` package.  I need a general way to specify the local 
# variables, though.
def error(x):
    if x == 'none':
        return nullcontext()

    err_type = eval_appcli(x['type'])
    err_messages = x.get('message', [])
    if not isinstance(err_messages, list):
        err_messages = list(err_messages)

    @contextmanager
    def raises():
        with pytest.raises(err_type) as err:
            yield

        for msg in err_messages:
            err.match(msg)

    return raises()

