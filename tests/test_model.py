#!/usr/bin/env python3

import byoc
import pytest
import parametrize_from_file

from voluptuous import Schema, Or, Optional, Coerce
from more_itertools import zip_equal
from param_helpers import *

class DummyObj:
    pass

class DummyConfig(byoc.Config):

    def __init__(self, layers):
        self.layers = layers

    def load(self, obj):
        return layers

@parametrize_from_file(
        schema=Schema({
            'obj': with_byoc.exec(get=get_obj),
            'init_layers': eval_obj_layers,
            'load_layers': eval_obj_layers,
            Optional('reload_layers', default={}): eval_obj_layers,
        })
)
def test_init_load_reload(obj, init_layers, load_layers, reload_layers):
    if not reload_layers:
        reload_layers = load_layers

    byoc.init(obj)
    assert collect_layers(obj) == init_layers

    try:
        obj.load()
    except AttributeError:
        byoc.load(obj)

    assert collect_layers(obj) == load_layers

    try:
        obj.reload()
    except AttributeError:
        byoc.reload(obj)

    assert collect_layers(obj) == reload_layers

def test_reload_instead_of_init():

    class DummyConfig(byoc.Config):
        def __init__(self, obj):
            super().__init__(obj)
            self.x = 0
        def load(self):
            self.x += 1
            yield byoc.DictLayer({'x': self.x})

    class DummyObj:
        __config__ = [DummyConfig]
        x = byoc.param()

    obj = DummyObj()
    byoc.reload(obj)
    assert obj.x == 1

    byoc.reload(obj)
    assert obj.x == 2

@parametrize_from_file(
        schema=Schema({
            'obj': with_byoc.exec(get=get_obj),
            'layers': eval_obj_layers,
        }),
)
def test_collect_layers(obj, layers):
    assert collect_layers(obj) == layers

def test_share_configs_mutable():

    class DummyConfigA(byoc.Config):
        def load(self):
            yield byoc.DictLayer(self.obj.a, location='a')
    
    class DummyConfigB(byoc.Config):
        def load(self):
            yield byoc.DictLayer(self.obj.b, location='b')

    class DummyDonor:
        __config__ = [DummyConfigB]

    class DummyAcceptor:
        __config__ = [DummyConfigA]

    donor = DummyDonor()
    donor.a = {'x': 1}  # decoy
    donor.b = {'x': 2}

    acceptor = DummyAcceptor()
    acceptor.a = {'x': 3}
    acceptor.b = {'x': 4}  # decoy

    byoc.load(donor)
    byoc.load(acceptor)

    assert collect_layers(donor) == {
            0: [
                DictLayerWrapper({'x': 2}, location='b'),
            ],
    }
    assert collect_layers(acceptor) == {
            0: [
                DictLayerWrapper({'x': 3}, location='a'),
            ],
    }

    byoc.share_configs(donor, acceptor)
    byoc.reload(donor)
    byoc.reload(acceptor)

    assert collect_layers(donor) == {
            0: [
                DictLayerWrapper({'x': 2}, location='b'),
            ],
    }
    assert collect_layers(acceptor) == {
            0: [
                DictLayerWrapper({'x': 3}, location='a'),
            ],
            1: [
                DictLayerWrapper({'x': 2}, location='b'),
            ],
    }

    # Reloading donor updates acceptor:
    donor.b = {'x': 5}
    byoc.reload(donor)

    assert collect_layers(donor) == {
            0: [
                DictLayerWrapper({'x': 5}, location='b'),
            ],
    }
    assert collect_layers(acceptor) == {
            0: [
                DictLayerWrapper({'x': 3}, location='a'),
            ],
            1: [
                DictLayerWrapper({'x': 5}, location='b'),
            ],
    }

def test_get_config_factories():

    sentinel = object()
    class Obj:
        __config__ = sentinel

    obj = Obj()
    assert byoc.model.get_config_factories(obj) is sentinel

def test_get_config_factories_err():
    obj = DummyObj()

    with pytest.raises(byoc.ApiError) as err:
        byoc.model.get_config_factories(obj)

    assert err.match('object not configured for use with byoc')
    assert err.match(no_templates)

@parametrize_from_file(
        schema=Schema({
            'obj': with_byoc.exec(get=get_obj, defer=True),
            'param': str,
            'expected': eval_meta,
        }),
)
def test_get_meta(obj, param, expected):
    obj = obj()
    meta = byoc.get_meta(obj, param)
    assert meta == expected
