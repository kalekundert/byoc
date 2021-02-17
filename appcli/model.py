#!/usr/bin/env python3

from .utils import lookup, noop
from .errors import ScriptError, ConfigError

CONFIG_ATTR = '__config__'
META_ATTR = '__appcli__'

UNSPECIFIED = object()

class Meta:

    def __init__(self, obj):
        self.bound_configs = [BoundConfig(x) for x in get_configs(obj)]
        self.param_states = {}
        self.cache_version = 0
        self.load_callbacks = get_load_callbacks(obj).values()

class BoundConfig:

    def __init__(self, config):
        self.config = config
        self.layers = []
        self.is_loaded = False

    def __repr__(self):
        return f'BoundConfig({self.config.__class__.__name__}, layers={self.layers!r}, is_loaded={self.is_loaded!r})'

    def __iter__(self):
        yield from self.layers

    def load(self, obj):
        self.layers = list(self.config.load(obj))
        for layer in self.layers:
            layer.config = self.config
        self.is_loaded = True

class BoundKey:
    
    def __init__(self, bound_config, key, cast):
        self.bound_config = bound_config
        self.key = key
        self.cast = cast

    def __repr__(self):
        return f'BoundKey({self.bound_config!r}, key={self.key!r}, cast={self.cast!r})'

def init(obj):
    if hasattr(obj, META_ATTR):
        return False

    setattr(obj, META_ATTR, Meta(obj))

    _load_configs(
            obj,
            predicate=lambda g: g.config.autoload,
            force_callback=lambda p: p._load_default(obj) is not UNSPECIFIED,
    )

    return True

def load(obj, config_cls=None):
    init(obj)

    _load_configs(
            obj,
            predicate=lambda g: (
                not g.is_loaded and
                _is_selected_by_cls(g.config, config_cls)
            ),
    )

def reload(obj, config_cls=None):
    if init(obj):
        return

    _load_configs(
            obj,
            predicate=lambda g: (
                g.is_loaded and 
                _is_selected_by_cls(g.config, config_cls)
            ),
    )

def get_meta(obj):
    return getattr(obj, META_ATTR)

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

def get_bound_configs(obj):
    return get_meta(obj).bound_configs

def get_cache_version(obj):
    return get_meta(obj).cache_version

def get_load_callbacks(obj):
    from .configs.on_load import OnLoad

    hits = {}

    for cls in reversed(obj.__class__.__mro__):
        for k, v in cls.__dict__.items():
            if isinstance(v, OnLoad):
                hits[k] = v

    return hits

def get_param_states(obj):
    return get_meta(obj).param_states

def iter_values(obj, bound_keys, default=UNSPECIFIED):
    locations = []
    have_value = False

    for bound_key in bound_keys:
        for layer in bound_key.bound_config:
            loc = layer.location
            locations.append((bound_key.key, loc() if callable(loc) else loc))

            try:
                value = lookup(layer.values, bound_key.key)
            except KeyError:
                pass
            else:
                try:
                    yield bound_key.cast(value)
                except Exception as err1:
                    err2 = ConfigError(
                            value=value,
                            function=bound_key.cast,
                            key=bound_key.key,
                            location=locations[-1][1],
                    )
                    err2.brief = "can't cast {value!r} using {function!r}"
                    err2.info += "read {key!r} from {location}"
                    err2.blame += str(err1)
                    raise err2 from err1
                else:
                    have_value = True

    if default is not UNSPECIFIED:
        have_value = True
        yield default

    if not have_value:
        configs = get_configs(obj)
        err = ConfigError(
                "can't find value for parameter",
                obj=obj,
                locations=locations,
                bound_keys=bound_keys,
        )

        if not configs:
            err.data.config_attr = CONFIG_ATTR
            err.blame += "`{obj.__class__.__qualname__}.{config_attr}` is empty"
            err.blame += "nowhere to look for values"

        elif not locations:
            from more_itertools import unique_everseen
            err.blame += lambda e: '\n'.join((
                "the following configs were found, but none yielded any layers:", *(
                    repr(bc.config) for bc in unique_everseen(
                        bk.bound_config for bk in e.bound_keys
                    )
                )
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

        raise err


def _load_configs(obj, predicate, force_callback=lambda p: False):
    meta = get_meta(obj)
    meta.bound_configs, bound_configs = [], meta.bound_configs
    meta.cache_version += 1
    updated_configs = []

    # Rebuild the `bound_configs` list from scratch and iterate through the 
    # configs in reverse order so that each config, when being loaded, can make 
    # use of values loaded by previous configs but not upcoming ones.
    for bound_config in reversed(bound_configs):
        if predicate(bound_config):
            bound_config.load(obj)
            updated_configs.append(bound_config.config)

        meta.bound_configs.insert(0, bound_config)
        meta.cache_version += 1

    for callback in meta.load_callbacks:
        if callback.is_relevant(updated_configs):
            callback(obj)

def _is_selected_by_cls(config, config_cls):
    return not config_cls or isinstance(config, config_cls)


