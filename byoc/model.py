#!/usr/bin/env python3

from .errors import ApiError

CONFIG_ATTR = '__config__'
STATE_ATTR = '__byoc__'

UNSPECIFIED = object()

class State:

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

    def load(self):
        # While it's tempting to defer actually loading the config until the 
        # layers are needed (e.g. in `__iter__()`), this doesn't work.  The 
        # problem is that configs are allowed to access previous (but not 
        # upcoming) configs during loading.  If loading is deferred, the object 
        # won't have the appropriate configs in place anymore.
        #
        # It may be possible to defer loading configs that promise not to 
        # access prior configs during loading.  But my initial instinct is that 
        # this would be too likely to cause bugs, and too unlikely to actually 
        # save any time.  See #11 for more discussion.
        self.layers = list(self.config.load())
        self.is_loaded = True

def init(obj):
    if hasattr(obj, STATE_ATTR):
        return False

    setattr(obj, STATE_ATTR, State(obj))

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
    state = get_state(obj)
    i = len(state.wrapped_configs)
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

    state = get_state(obj)
    state.wrapped_configs = \
            state.wrapped_configs[:i] + \
            new_wrapped_configs + \
            state.wrapped_configs[i:]

    _load_configs(
            obj,
            predicate=lambda wc: wc in new_wrapped_configs
    )

def share_configs(donor, acceptor):
    init(donor); init(acceptor)

    donor_state = get_state(donor)
    acceptor_state = get_state(acceptor)

    acceptor_state.wrapped_configs.extend(donor_state.wrapped_configs)
    acceptor_state.cache_version += 1

def get_state(obj):
    return getattr(obj, STATE_ATTR)

def get_config_factories(obj):
    try:
        return getattr(obj, CONFIG_ATTR)
    except AttributeError:
        err = ApiError(
                obj=obj,
                config_attr=CONFIG_ATTR,
        )
        err.brief = "object not configured for use with byoc"
        err.blame += "{obj!r} has no '{config_attr}' attribute"
        raise err

def get_wrapped_configs(obj):
    return get_state(obj).wrapped_configs

def get_cache_version(obj):
    return get_state(obj).cache_version

def get_load_callbacks(obj):
    from .configs.on_load import OnLoad

    hits = {}

    for cls in reversed(obj.__class__.__mro__):
        for k, v in cls.__dict__.items():
            if isinstance(v, OnLoad):
                hits[k] = v

    return hits

def get_param_states(obj):
    return get_state(obj).param_states

def get_meta(obj, param):
    from .meta import NeverAccessedMeta

    try:
        states = get_param_states(obj)
    except AttributeError:
        return NeverAccessedMeta()

    try:
        state = states[param]
    except KeyError:
        return NeverAccessedMeta()

    return state.meta


def _load_configs(obj, predicate):
    state = get_state(obj)
    state.wrapped_configs, wrapped_configs = [], state.wrapped_configs
    state.cache_version += 1
    updated_configs = []

    # Rebuild the `wrapped_configs` list from scratch and iterate through the 
    # configs in reverse order so that each config, when being loaded, can make 
    # use of values loaded by previous configs but not upcoming ones.
    for wrapped_config in reversed(wrapped_configs):
        if predicate(wrapped_config):
            wrapped_config.load()
            updated_configs.append(wrapped_config.config)

        state.wrapped_configs.insert(0, wrapped_config)
        state.cache_version += 1

    for callback in state.load_callbacks:
        if callback.is_relevant(updated_configs):
            callback(obj)

def _is_selected_by_cls(config, config_cls):
    return not config_cls or isinstance(config, config_cls)


