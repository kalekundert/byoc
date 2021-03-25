#!/usr/bin/env python3

import appcli
import pytest
from voluptuous import Schema, And, Or, Optional, Invalid, Coerce
from more_itertools import only
from unittest.mock import Mock

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

def eval_appcli(code, globals=None, **kw_globals):
    if globals is None:
        globals = {}

    globals['appcli'] = appcli
    globals.update(kw_globals)

    try:
        return eval(code, globals)
    except Exception as err:
        raise Invalid(str(err)) from err

def eval_layers(layers, globals=None, **kw_globals):
    schema = Schema({
        Coerce(int): Or(
            [lambda x: eval_layer(x, globals, **kw_globals)],
            empty_list,
        ),
    })
    return schema(layers)

def eval_layer(layer, globals=None, **kw_globals):
    schema = Schema(Or(str, {
        'values': eval,
        'location': str,
    }))
    layer = schema(layer)
    layer = eval_appcli(layer, globals, **kw_globals) \
            if isinstance(layer, str) else appcli.Layer(**layer)
    return LayerWrapper(layer)

def exec_appcli(code, globals=None, **kw_globals):
    if globals is None:
        globals = {}

    globals['appcli'] = appcli
    globals.update(kw_globals)

    try:
        exec(code, globals)
    except Exception as err:
        raise Invalid(str(err)) from err

    return globals

def exec_obj(code, globals=None, **kw_globals):
    locals = exec_appcli(code, globals, **kw_globals) 
    try:
        return locals['obj']
    except KeyError:
        return locals['DummyObj']()

def exec_config(code, globals=None, **kw_globals):
    locals = exec_appcli(code, globals, **kw_globals)
    try:
        return locals['config']
    except KeyError:
        return locals['DummyConfig']()

def collect_layers(obj):
    bound_configs = appcli.model.get_bound_configs(obj)
    return {
            i: bound_config.layers
            for i, bound_config in enumerate(bound_configs)
    }
def find_param(obj, name=None):
    class_attrs = obj.__class__.__dict__

    if name:
        return class_attrs[name]
    else:
        params = (
                x for x in class_attrs.values()
                if isinstance(x, appcli.param)
        )
        default = appcli.param()
        default.__set_name__(obj.__class__, '')
        return only(params, default)

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
        Optional(k, default=Mock()): Or(Mock, v)
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

    # Normally I'd use `@contextmanager` to make a context manager like this, 
    # but generator-based context managers cannot be reused.  This is a problem 
    # for tests, because if a test using this context manager is parametrized, 
    # the same context manager instance will need to be reused multiple times.  
    # The only way to support this is to implement the context manager from 
    # scratch.

    class expect_error:

        def __enter__(self):
            self.raises = pytest.raises(err_type)
            self.err = self.raises.__enter__()

        def __exit__(self, *args):
            if self.raises.__exit__(*args):
                for msg in err_messages:
                    self.err.match(msg)
                return True

    return expect_error()

