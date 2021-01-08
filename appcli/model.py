#!/usr/bin/env python3

from .layers import Layer, LayerGroup
from .utils import lookup
from .errors import ScriptError, ConfigError
from collections.abc import Sequence
from more_itertools import unique_justseen

CONFIG_ATTR = '__config__'
META_ATTR = '__appcli__'
SENTINEL = object()

class Meta:

    def __init__(self, obj):
        self.layer_groups = [LayerGroup(x) for x in get_configs(obj)]
        self.param_states = {}
        self.cache_version = 0

def init(obj):
    if hasattr(obj, META_ATTR):
        return False

    setattr(obj, META_ATTR, Meta(obj))

    _load_groups(
            obj,
            predicate=lambda g: g.config.autoload,
            force_callback=lambda p: p._default is not SENTINEL
    )
    return True

def load(obj, config_cls=None):
    init(obj)

    _load_groups(
            obj,
            predicate=lambda g: (
                not g.is_loaded and
                _is_selected_by_cls(g.config, config_cls)
            ),
    )

def reload(obj, config_cls=None):
    if init(obj):
        return

    _load_groups(
            obj,
            predicate=lambda g: (
                g.is_loaded and 
                _is_selected_by_cls(g.config, config_cls)
            ),
    )

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

def get_meta(obj):
    return getattr(obj, META_ATTR)

def get_cache_version(obj):
    return get_meta(obj).cache_version

def get_params(obj):
    from .params import param

    params = {}

    for cls in reversed(obj.__class__.__mro__):
        for k, v in cls.__dict__.items():
            if isinstance(v, param):
                params[k] = v

    return params

def init_param_state(obj, name, state):
    """
    Provide a state object for the given parameter.

    It is safe to call this function any number of times.
    """
    return get_meta(obj).param_states.setdefault(name, state)

def iter_layers(obj):
    for group in get_meta(obj).layer_groups:
        yield from group

def iter_values(obj, key_map, default=SENTINEL):
    locations = []
    have_value = False

    for layer in iter_layers(obj):
        for key, cast in key_map.get(layer.config, []):
            loc = layer.location
            locations.append((key, loc() if callable(loc) else loc))

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
                key_map=key_map,
        )

        if not configs:
            err.data.config_attr = CONFIG_ATTR
            err.blame += "`{obj.__class__.__qualname__}.{config_attr}` is empty"
            err.blame += "nowhere to look for values"

        elif not key_map:
            err.blame += "no configs are associated with this parameter"

        elif not locations:
            err.blame += lambda e: '\n'.join((
                "the following configs were found, but none yielded any layers:",
                *(repr(x) for x in e.key_map)
            ))
            err.hints += f"did you forget to call `appcli.load()`?"

        else:
            err.info += lambda e: '\n'.join((
                    "the following locations were searched:", *(
                        f'{loc}: {key}'
                        for key, loc in e.locations
                    )
            ))
            err.hints += "did you mean to provide a default?"

        raise err from None


def _load_groups(obj, predicate, force_callback=lambda p: False):
    meta = get_meta(obj)
    meta.layer_groups, groups = [], meta.layer_groups
    meta.cache_version += 1
    updated_configs = set()

    # Rebuild the `layer_groups` list from scratch and iterate through the 
    # groups in reverse order so that each config, when being loaded, can make 
    # use of values loaded by previous configs but not upcoming ones.
    for group in reversed(groups):
        if predicate(group):
            group.load(obj)
            updated_configs.add(group.config)

        meta.layer_groups.insert(0, group)
        meta.cache_version += 1

    callbacks = set()

    for param in get_params(obj).values():
        key_map = param._load_key_map(obj)
        is_param_affected = updated_configs.intersection(key_map.keys())

        if is_param_affected or force_callback(param):
            callbacks.add(param._set)

    for callback in callbacks:
        callback(obj)

def _is_selected_by_cls(config, config_cls):
    return not config_cls or isinstance(config, config_cls)


