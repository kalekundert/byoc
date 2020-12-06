#!/usr/bin/env python3

from .config import Layer, PendingLayer
from .errors import ScriptError
from collections.abc import Sequence
from more_itertools import unique_everseen

CONFIG_ATTR = '__config__'
META_ATTR = '__appcli__'

class Meta:

    def __init__(self):
        self.layers = []
        self.overrides = {}


def init(obj):
    if hasattr(obj, META_ATTR):
        return

    meta = Meta(); setattr(obj, META_ATTR, meta)
    configs = get_configs(obj)

    # It's important that we're modifying the "live" list of layers in-place.  
    # This allows configs to make use of values loaded by previous configs.
    for config in reversed(configs):
        if config.require_explicit_load:
            meta.layers[:0] = [PendingLayer(config)]
        else:
            meta.layers[:0] = load_config(config, obj)

def load(obj):
    init(obj)

    meta = get_meta(obj)
    meta.layers, existing = [], meta.layers

    # It's important that we're modifying the "live" list of layers in-place.  
    # This allows configs to make use of values loaded by previous configs.
    for layer in reversed(existing):
        if isinstance(layer, PendingLayer):
            meta.layers[:0] = load_config(layer.config, obj)
        else:
            meta.layers[:0] = [layer]

def get_configs(obj):
    try:
        return getattr(obj, CONFIG_ATTR)
    except AttributeError:
        err = ScriptError(
                obj=obj,
                configs_attr=CONFIG_ATTR,
        )
        err.brief = "object not configured for use with appcli"
        err.blame += "{obj!r} has no '{config_attr}' attribute"
        raise err

def load_config(config, obj):
    layers = config.load(obj)

    if isinstance(layers, Sequence):
        pass
    elif isinstance(layers, Layer):
        layers = [layers]
    else:
        err = ScriptError(
                config=config,
                retval=layers,
        )
        err.brief = "Config.load() must return `Layer` or `List[Layer]`"
        err.blame += "{config!r} returned {retval}"
        raise err

    for layer in layers:
        layer.config = config

    return layers

def get_meta(obj):
    return getattr(obj, META_ATTR)

def get_layers(obj):
    return get_meta(obj).layers

def get_overrides(obj):
    return get_meta(obj).overrides

def iter_active_layers(obj):
    yield from (
            x for x in get_layers(obj)
            if not isinstance(x, PendingLayer)
    )

def get_key_groups(obj):
    configs = get_configs(obj)
    return list(unique_everseen(x.key_group for x in configs))

def get_cast_groups(obj):
    configs = get_configs(obj)
    return list(unique_everseen(x.cast_group for x in configs))
