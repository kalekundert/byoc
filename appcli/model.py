#!/usr/bin/env python3

from .layers import Layer, PendingLayer
from .utils import lookup
from .errors import ScriptError, ConfigError
from collections.abc import Sequence

CONFIG_ATTR = '__config__'
META_ATTR = '__appcli__'
SENTINEL = object()

class Meta:

    def __init__(self):
        self.layers = []
        self.overrides = {}

def init(obj):
    if hasattr(obj, META_ATTR):
        return

    meta = Meta(); setattr(obj, META_ATTR, meta)
    configs = get_configs(obj)

    # Modify the list of layers in-place and in reverse order so that 
    # Config.load() can make use of values loaded by previous configs.
    for config in reversed(configs):
        if config.autoload:
            meta.layers[:0] = load_config(config, obj)
        else:
            meta.layers[:0] = [PendingLayer(config)]

def load(obj, config_cls=None):
    init(obj)

    meta = get_meta(obj)
    meta.layers, existing = [], meta.layers

    def load_layer(layer, obj):
        if not isinstance(layer, PendingLayer):
            return [layer]

        if config_cls and not isinstance(layer.config, config_cls):
            return [layer]

        return load_config(layer.config, obj)

    # Modify the list of layers in-place and in reverse order so that 
    # Config.load() can make use of values loaded by previous configs.
    for layer in reversed(existing):
        meta.layers[:0] = load_layer(layer, obj)

def get_configs(obj):
    try:
        return getattr(obj, CONFIG_ATTR)
    except AttributeError:
        err = ScriptError(
                obj=obj,
                config_attr=CONFIG_ATTR,
        )
        err.brief = "object not configured for use with appcli"
        err.blame += "{obj!r} has no '{config_attr}' attribute"
        raise err

def load_config(config, obj):
    layers = list(config.load(obj))

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

def iter_values(obj, key_map, cast_map, default=SENTINEL):
    init(obj)

    locations = []
    have_value = False

    for layer in iter_active_layers(obj):
        try:
            key = key_map[layer.config]
        except KeyError:
            continue

        cast = cast_map.get(layer.config, lambda x: x)
        locations.append((key, layer.location))

        try:
            value = lookup(layer.values, key)
        except KeyError:
            pass
        else:
            try:
                yield cast(value)
            except Exception as err1:
                err2 = ConfigError(
                        value=value,
                        function=cast,
                        key=key,
                        location=layer.location,
                )
                err2.brief = "can't cast {value!r} using {function!r}"
                err2.info += "read {key!r} from {location}"
                err2.blame += str(err1)
                raise err2 from err1
            else:
                have_value = True

    if default is not SENTINEL:
        have_value = True
        yield default

    if not have_value:
        configs = get_configs(obj)
        err = ConfigError(
                "can't find value for parameter",
                obj=obj,
                locations=locations,
                configs=configs,
        )

        if not configs:
            err.data.config_attr = CONFIG_ATTR
            err.blame += "`{obj.__class__.__qualname__}.{config_attr}` is empty"
            err.blame += "nowhere to look for values"

        elif not locations:
            if get_layers(obj):
                err.blame += lambda e: '\n'.join((
                    "the following configs were found, but may not have been loaded:",
                    *(repr(x) for x in e.configs)
                ))
                err.hints += f"did you forget to call `appcli.load()`?"

            else:
                err.blame += lambda e: '\n'.join((
                    "the following configs were found, but none yielded any layers:",
                    *(repr(x) for x in e.configs)
                ))

        else:
            err.info += lambda e: '\n'.join((
                    "the following locations were searched:", *(
                        f'{loc}: {key}'
                        for key, loc in e.locations
                    )
            ))
            err.hints += "did you mean to provide a default?"

        raise err from None
