#!/usr/bin/env python3

from .utils import lookup, noop
from .errors import ScriptError, ConfigError

CONFIG_ATTR = '__config__'
META_ATTR = '__appcli__'

UNSPECIFIED = object()

class Meta:

    def __init__(self, obj):
        self.wrapped_configs = [
                WrappedConfig(cf(obj))
                for cf in get_config_factories(obj)
        ]
        self.param_states = {}
        self.cache_version = 0
        self.load_callbacks = get_load_callbacks(obj).values()

class WrappedConfig:

    def __init__(self, config):
        self.config = config
        self.layers = []
        self.is_loaded = False

    def __repr__(self):
        return f'{self.__class__.__name__}({self.config!r}, is_loaded={self.is_loaded!r})'

    def __iter__(self):
        yield from self.layers

    def __bool__(self):
        return bool(self.layers)

    def load(self):
        self.layers = list(self.config.load())
        self.is_loaded = True

class Log:
    
    def __init__(self):
        self.err = ConfigError()

    def info(self, message, **kwargs):
        self.err.put_info(message, **kwargs)

    def hint(self, message):
        if message not in self.err.hints:
            self.err.hints += message

    def make_error(self, brief):
        self.err.brief = brief
        return self.err

def init(obj):
    if hasattr(obj, META_ATTR):
        return False

    setattr(obj, META_ATTR, Meta(obj))

    _load_configs(
            obj,
            predicate=lambda wc: wc.config.autoload,
    )

    return True

def load(obj, config_cls=None):
    init(obj)

    _load_configs(
            obj,
            predicate=lambda wc: (
                not wc.is_loaded and
                _is_selected_by_cls(wc.config, config_cls)
            ),
    )

def reload(obj, config_cls=None):
    if init(obj):
        return

    _load_configs(
            obj,
            predicate=lambda wc: (
                wc.is_loaded and 
                _is_selected_by_cls(wc.config, config_cls)
            ),
    )

def append_config(obj, config_factory):
    append_configs(obj, [config_factory])

def append_configs(obj, config_factories):
    init(obj)
    meta = get_meta(obj)
    i = len(meta.wrapped_configs)
    insert_configs(obj, i, config_factories)

def prepend_config(obj, config_factory):
    prepend_configs(obj, [config_factory])

def prepend_configs(obj, config_factories):
    insert_configs(obj, 0, config_factories)

def insert_config(obj, i, config_factory):
    insert_configs(obj, i, [config_factory])

def insert_configs(obj, i, config_factories):
    init(obj)

    new_wrapped_configs = [
            WrappedConfig(cf(obj))
            for cf in config_factories
    ]

    meta = get_meta(obj)
    meta.wrapped_configs = \
            meta.wrapped_configs[:i] + \
            new_wrapped_configs + \
            meta.wrapped_configs[i:]

    _load_configs(
            obj,
            predicate=lambda wc: wc in new_wrapped_configs
    )

def share_configs(donor, acceptor):
    init(donor); init(acceptor)

    donor_meta = get_meta(donor)
    acceptor_meta = get_meta(acceptor)

    acceptor_meta.wrapped_configs.extend(donor_meta.wrapped_configs)
    acceptor_meta.cache_version += 1

def get_meta(obj):
    return getattr(obj, META_ATTR)

def get_config_factories(obj):
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

def get_wrapped_configs(obj):
    return get_meta(obj).wrapped_configs

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

def iter_values(getters, default=UNSPECIFIED):
    # It's important that this function is a generator.  This allows the `pick` 
    # argument to `param()` to pick, for example, the first value without 
    # having to calculate any subsequent values (which could be expensive).

    log = Log()
    have_value = False

    if not getters:
        log.info("nowhere to look for values")

    for getter in getters:
        for value in getter.iter_values(log):
            have_value = True
            yield getter.cast_value(value)

    if default is not UNSPECIFIED:
        have_value = True
        yield default
    else:
        log.hint("did you mean to provide a default?")

    if not have_value:
        raise log.make_error("can't find value for parameter")


def _load_configs(obj, predicate):
    meta = get_meta(obj)
    meta.wrapped_configs, wrapped_configs = [], meta.wrapped_configs
    meta.cache_version += 1
    updated_configs = []

    # Rebuild the `wrapped_configs` list from scratch and iterate through the 
    # configs in reverse order so that each config, when being loaded, can make 
    # use of values loaded by previous configs but not upcoming ones.
    for wrapped_config in reversed(wrapped_configs):
        if predicate(wrapped_config):
            wrapped_config.load()
            updated_configs.append(wrapped_config.config)

        meta.wrapped_configs.insert(0, wrapped_config)
        meta.cache_version += 1

    for callback in meta.load_callbacks:
        if callback.is_relevant(updated_configs):
            callback(obj)

def _is_selected_by_cls(config, config_cls):
    return not config_cls or isinstance(config, config_cls)


