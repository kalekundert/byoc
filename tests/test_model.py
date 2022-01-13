#!/usr/bin/env python3

import pytest
import parametrize_from_file
import appcli
from voluptuous import Schema, Or, Optional, Coerce
from more_itertools import zip_equal
from param_helpers import *

class DummyObj:
    pass

class DummyConfig(appcli.Config):

    def __init__(self, layers):
        self.layers = layers

    def load(self, obj):
        return layers

@parametrize_from_file(
        schema=Schema({
            'obj': with_appcli.exec(get=get_obj),
            'init_layers': eval_obj_layers,
            'load_layers': eval_obj_layers,
            Optional('reload_layers', default={}): eval_obj_layers,
        })
)
def test_init_load_reload(obj, init_layers, load_layers, reload_layers):
    if not reload_layers:
        reload_layers = load_layers

    appcli.init(obj)
    assert collect_layers(obj) == init_layers

    try:
        obj.load()
    except AttributeError:
        appcli.load(obj)

    assert collect_layers(obj) == load_layers

    try:
        obj.reload()
    except AttributeError:
        appcli.reload(obj)

    assert collect_layers(obj) == reload_layers

@parametrize_from_file(
        schema=Schema({
            'obj': with_appcli.exec(get=get_obj),
            'layers': eval_obj_layers,
        }),
)
def test_collect_layers(obj, layers):
    assert collect_layers(obj) == layers

def test_share_configs_mutable():

    class DummyConfigA(appcli.Config):
        def load(self):
            yield appcli.DictLayer(self.obj.a, location='a')
    
    class DummyConfigB(appcli.Config):
        def load(self):
            yield appcli.DictLayer(self.obj.b, location='b')

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

    appcli.load(donor)
    appcli.load(acceptor)

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

    appcli.share_configs(donor, acceptor)
    appcli.reload(donor)
    appcli.reload(acceptor)

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
    appcli.reload(donor)

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
    assert appcli.model.get_config_factories(obj) is sentinel

def test_get_config_factories_err():
    obj = DummyObj()

    with pytest.raises(appcli.ApiError) as err:
        appcli.model.get_config_factories(obj)

    assert err.match('object not configured for use with appcli')
    assert err.match(no_templates)

@parametrize_from_file(
        schema=Schema({
            'obj': with_appcli.exec(get=get_obj, defer=True),
            'param': str,
            'expected': eval_meta,
        }),
)
def test_get_meta(obj, param, expected):
    obj = obj()
    meta = appcli.get_meta(obj, param)
    assert meta == expected
