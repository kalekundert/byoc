#!/usr/bin/env python3

import byoc
import pytest
import parametrize_from_file
from voluptuous import Schema, Optional, Or
from param_helpers import *

@parametrize_from_file(
        schema=Schema({
            'obj': with_byoc.exec(get=get_obj, defer=True),
            **with_byoc.error_or({
                'expected': {str: with_py.eval},
            }),
        }),
)
def test_param(obj, expected, error):
    with error:
        obj = obj.exec()
        for param, value in expected.items():
            assert getattr(obj, param) == value

@pytest.mark.parametrize('dynamic', [True, False])
def test_param_cache_exc(dynamic):
    # Make sure exceptions are cached just like values are.

    class DummyConfig(byoc.Config):
        def load(self):
            yield byoc.DictLayer(self.obj.values)

    class DummyObj:
        __config__ = [DummyConfig]
        x = byoc.param(dynamic=dynamic)

    obj = DummyObj()

    # Before providing a value:
    obj.values = {}
    assert not hasattr(obj, 'x')

    # After providing a value, before updating the cache:
    obj.values['x'] = 1
    assert (obj.x == 1) if dynamic else not hasattr(obj, 'x')

    # After updating the cache:
    byoc.reload(obj)
    assert obj.x == 1

@pytest.mark.parametrize('dynamic', [True, False])
def test_param_cache_reload(dynamic):

    class BackgroundConfig(byoc.Config):
        def load(self):
            yield byoc.DictLayer(values={'x': -1})

    class ForegroundConfig(byoc.Config):
        values = {'x': 1}

        def load(self):
            # Access the value of the parameter during the load function so 
            # that we can tell if an intermediate value from the loading 
            # process (e.g.  -1) is mistakenly saved as the cache value.
            self.obj.x

            yield byoc.DictLayer(values=self.values)
    
    class DummyObj:
        __config__ = [ForegroundConfig, BackgroundConfig]
        x = byoc.param(dynamic=dynamic)

    
    obj = DummyObj()
    assert obj.x == 1

    # Before updating the cache:
    ForegroundConfig.values['x'] = 2
    assert obj.x == (2 if dynamic else 1)

    # After updating the cache:
    byoc.reload(obj)
    assert obj.x == 2

def test_param_cache_instance_values():
    # Test to make sure the independent instances have independent caches.

    class Background(byoc.Config):
        def load(self):
            yield byoc.DictLayer(values={'x': 1})
    
    class Foreground(byoc.Config):
        autoload = False
        def load(self):
            yield byoc.DictLayer(values={'x': 2})
    
    class DummyObj:
        __config__ = [Foreground, Background]
        x = byoc.param()

    o1 = DummyObj()
    o2 = DummyObj()

    assert o1.x == 1
    assert o2.x == 1

    byoc.model.load(o2)

    assert o1.x == 1
    assert o2.x == 2
    
def test_param_cache_instance_key_map():
    # Test to make sure that key map values, if cached, aren't shared between 
    # instances of different classes.
    
    class DummyConfig(byoc.Config):
        def load(self):
            yield byoc.DictLayer(values={'x': 1})
    
    class DecoyConfig(byoc.Config):
        def load(self):
            yield byoc.DictLayer(values={'x': 2})
    
    class ParentObj:
        x = byoc.param()
    
    class DummyObj(ParentObj):
        __config__ = [DummyConfig]
    
    class DecoyObj(ParentObj):
        __config__ = [DecoyConfig]
    
    decoy = DecoyObj()
    assert decoy.x == 2

    obj = DummyObj()
    assert obj.x == 1

def test_param_cache_get():
    # Test to make sure that the get function is called on every parameter 
    # access, even if the underlying value is cached.
    
    class DummyConfig(byoc.Config):

        def load(self):
            yield byoc.DictLayer(values={'x': 1})
    
    class DummyObj:
        __config__ = [DummyConfig]

        def __init__(self):
            self.y = 0

        def _update_y(self, x):
            self.y += 1
            return x

        x = byoc.param(get=_update_y)
    
    obj = DummyObj()
    assert obj.y == 0

    assert obj.x == 1
    assert obj.y == 1

    assert obj.x == 1
    assert obj.y == 2

    assert obj.x == 1
    assert obj.y == 3

def test_param_set_non_comparable():
    class NonComparable:
        def __eq__(self, other):
            raise AssertionError

    class DummyObj:
        __config__ = []
        x = byoc.param()

    obj = DummyObj()
    obj.x = nc = NonComparable()

    # This parameter access should not attempt any comparisons.
    assert obj.x is nc


def locals_or_ab(locals):
    if locals:
        shared = dict(byoc=byoc)
        exec(locals, {}, shared)
        return shared

    else:
        class A(byoc.Config): pass
        class B(byoc.Config): pass
        return dict(byoc=byoc, A=A, B=B, a=A(), b=B())

def wrap_key_map(map, x):
    return {
            cls: [
                (key, cast(x))
                for key, cast in keys_casts
            ]
            for cls, keys_casts in map.items()
    }
