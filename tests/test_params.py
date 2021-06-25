#!/usr/bin/env python3

import appcli
import pytest
import parametrize_from_file
from voluptuous import Schema, Optional, Or
from schema_helpers import *

@parametrize_from_file(
        schema=Schema({
            'obj': exec_obj,
            'expected': {str: eval},
        })
)
def test_param(obj, expected):
    for attr, value in expected.items():
        print(attr, value)
        assert getattr(obj, attr) == value

def test_param_init_err():
    with pytest.raises(appcli.ScriptError) as err:
        appcli.param(default=1, default_factory=list)

    assert err.match(r"can't specify 'default' and 'default_factory'")
    assert err.match(r"default: 1")
    assert err.match(r"default_factory: <class 'list'>")

@pytest.mark.parametrize('dynamic', [True, False])
def test_param_cache_exc(dynamic):
    # Make sure exceptions are cached just like values are.

    class DummyConfig(appcli.Config):
        def load(self):
            yield appcli.DictLayer(self.obj.values)

    class DummyObj:
        __config__ = [DummyConfig]
        x = appcli.param(dynamic=dynamic)

    obj = DummyObj()

    # Before providing a value:
    obj.values = {}
    assert not hasattr(obj, 'x')

    # After providing a value, before updating the cache:
    obj.values['x'] = 1
    assert (obj.x == 1) if dynamic else not hasattr(obj, 'x')

    # After updating the cache:
    appcli.reload(obj)
    assert obj.x == 1

@pytest.mark.parametrize('dynamic', [True, False])
def test_param_cache_reload(dynamic):

    class BackgroundConfig(appcli.Config):
        def load(self):
            yield appcli.DictLayer(values={'x': -1})

    class ForegroundConfig(appcli.Config):
        values = {'x': 1}

        def load(self):
            # Access the value of the parameter during the load function so 
            # that we can tell if an intermediate value from the loading 
            # process (e.g. -1) is mistakenly saved as the cache value.
            self.obj.x

            yield appcli.DictLayer(values=self.values)
    
    class DummyObj:
        __config__ = [ForegroundConfig, BackgroundConfig]
        x = appcli.param(dynamic=dynamic)

    
    obj = DummyObj()
    assert obj.x == 1

    # Before updating the cache:
    ForegroundConfig.values['x'] = 2
    assert obj.x == (2 if dynamic else 1)

    # After updating the cache:
    appcli.reload(obj)
    assert obj.x == 2

def test_param_cache_instance_values():
    # Test to make sure the independent instances have independent caches.

    class Background(appcli.Config):
        def load(self):
            yield appcli.DictLayer(values={'x': 1})
    
    class Foreground(appcli.Config):
        autoload = False
        def load(self):
            yield appcli.DictLayer(values={'x': 2})
    
    class DummyObj:
        __config__ = [Foreground, Background]
        x = appcli.param()

    o1 = DummyObj()
    o2 = DummyObj()

    assert o1.x == 1
    assert o2.x == 1

    appcli.model.load(o2)

    assert o1.x == 1
    assert o2.x == 2
    
def test_param_cache_instance_key_map():
    # Test to make sure that key map values, if cached, aren't shared between 
    # instances of different classes.
    
    class DummyConfig(appcli.Config):
        def load(self):
            yield appcli.DictLayer(values={'x': 1})
    
    class DecoyConfig(appcli.Config):
        def load(self):
            yield appcli.DictLayer(values={'x': 2})
    
    class ParentObj:
        x = appcli.param()
    
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
    
    class DummyConfig(appcli.Config):

        def load(self):
            yield appcli.DictLayer(values={'x': 1})
    
    class DummyObj:
        __config__ = [DummyConfig]

        def __init__(self):
            self.y = 0

        def _update_y(self, x):
            self.y += 1
            return x

        x = appcli.param(get=_update_y)
    
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
        x = appcli.param()

    obj = DummyObj()
    obj.x = nc = NonComparable()

    # This attribute access should not attempt any comparisons.
    assert obj.x is nc


def locals_or_ab(locals):
    if locals:
        shared = dict(appcli=appcli)
        exec(locals, {}, shared)
        return shared

    else:
        class A(appcli.Config): pass
        class B(appcli.Config): pass
        return dict(appcli=appcli, A=A, B=B, a=A(), b=B())

def wrap_key_map(map, x):
    return {
            cls: [
                (key, cast(x))
                for key, cast in keys_casts
            ]
            for cls, keys_casts in map.items()
    }
