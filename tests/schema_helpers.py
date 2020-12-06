#!/usr/bin/env python3

import appcli
import pytest
from schema import Schema, Use, And, Or, Optional
from contextlib import contextmanager, nullcontext

class LayerWrapper:

    def __init__(self, layer):
        self.layer = layer

    def __repr__(self):
        return f'LayerWrapper({self.layer!r})'

    def __eq__(self, other):
        if isinstance(self.layer, appcli.Layer):
            return all((
                    isinstance(other, appcli.Layer),
                    self.layer.values == other.values,
                    self.layer.location == str(other.location),
            ))

        if isinstance(self.layer, appcli.PendingLayer):
            return all((
                    isinstance(other, appcli.PendingLayer),
                    self.layer.config is other.config,
            ))

        raise AssertionError(f"expected `Layer` or `PendingLayer`, not {self.layer}")

def eval_appcli(code, **locals):
    globals = dict(appcli=appcli)
    return eval(code, globals, locals)

def eval_layers(layers, **locals):
    schema = Schema([Use(lambda x: eval_layer(x, **locals))])
    return schema.validate(layers)

def eval_layer(layer, **locals):
    schema = Schema(Or(str, {
        'values': Use(eval),
        'location': str,
    }))
    layer = schema.validate(layer)
    layer = eval(layer) if isinstance(layer, str) else appcli.Layer(**layer)
    return LayerWrapper(layer)

def exec_appcli(code):
    globals = dict(appcli=appcli)
    exec(code, globals)
    return globals

def exec_obj(code):
    locals = exec_appcli(code) 
    try:
        return locals['obj']
    except KeyError:
        return locals['DummyObj']()

def exec_config(code):
    locals = exec_appcli(code) 
    try:
        return locals['config']
    except KeyError:
        return locals['DummyConfig']()

empty_list = And('', Use(lambda x: []))
empty_dict = And('', Use(lambda x: {}))
no_templates = '^[^{}]*$'

def error_or(**expected):
    schema = {}

    # Either specify an error or an expected value, not both.
    # KBK: This doesn't work for some reason.
    #schema[Or('error', *expected, only_one=True)] = object

    schema[Optional('error', default=nullcontext())] = Use(error)

    schema.update({
        Optional(k, default=None): v
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
    err_messages.append(no_templates)

    @contextmanager
    def raises():
        with pytest.raises(err_type) as err:
            yield

        for msg in err_messages:
            err.match(msg)

    return raises()

