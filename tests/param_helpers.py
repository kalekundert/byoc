#!/usr/bin/env python3

import appcli
import pytest

from parametrize_from_file.voluptuous import Namespace, empty_ok
from voluptuous import Schema, And, Or, Optional, Invalid, Coerce
from unittest.mock import Mock

with_py = Namespace('from operator import itemgetter')
with_appcli = Namespace(appcli)

class LayerWrapper:

    def __init__(self, layer):
        self.layer = layer

    def __repr__(self):
        return f'LayerWrapper({self.layer!r})'

    def __eq__(self, other):
        def str_or_none(x):
            return str(x) if x is not None else x

        if not isinstance(other, appcli.Layer):
            return False

        if self.layer.values != other.values:
            return False

        if self.layer.location != str_or_none(other.location):
            return False

        if hasattr(self.layer, 'root_key') and self.layer.root_key != other.root_key:
            return False

        if hasattr(self.layer, 'schema') and self.layer.schema != other.schema:
            return False

        return True

class DictLayerWrapper(LayerWrapper):

    def __init__(self, *args, **kwargs):
        super().__init__(appcli.DictLayer(*args, **kwargs))

def eval_obj_layers(layers):
    schema = Schema(empty_ok({
        Coerce(int): eval_config_layers,
    }))
    return schema(layers)

def eval_config_layers(layers):
    schema = Schema(empty_ok([eval_layer]))
    return schema(layers)

def eval_layer(layer):
    schema = Schema(Or(str, {
        'values': eval,
        'location': str,
        Optional('root_key'): eval,
        Optional('schema'): eval,
    }))
    layer = schema(layer)
    layer = with_appcli.eval(layer) if isinstance(layer, str) else \
            appcli.DictLayer(**layer)
    return LayerWrapper(layer)

def collect_layers(obj):
    wrapped_configs = appcli.model.get_wrapped_configs(obj)
    return {
            i: wc.layers
            for i, wc in enumerate(wrapped_configs)
    }

def find_param(obj, name=None):
    from more_itertools import only
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

def get_obj_or_cls(obj_name, cls_name=None):
    if not cls_name:
        cls_name = f'Dummy{obj_name.title()}'

    def get(ns):
        try:
            return ns[obj_name]
        except KeyError:
            return ns[cls_name]()

    return get

get_obj = get_obj_or_cls('obj')
get_config = get_obj_or_cls('config')
no_templates = '^[^{}]*$'
