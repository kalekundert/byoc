#!/usr/bin/env python3

from .. import model
from ..errors import AppcliError, ConfigError, ScriptError
from ..model import UNSPECIFIED
from ..utils import noop
from more_itertools import first

class param:

    class _State:

        def __init__(self, default):
            self.bound_keys = []
            self.setattr_value = UNSPECIFIED
            self.cache_value = UNSPECIFIED
            self.cache_version = -1
            self.default_value = default

    def __init__(
            self,
            *keys,
            cast=noop,
            pick=first,
            default=UNSPECIFIED,
            default_factory=UNSPECIFIED,
            ignore=UNSPECIFIED,
            get=lambda obj, x: x,
            dynamic=False,
    ):
        self._keys = keys
        self._cast = cast
        self._pick = pick
        self._default_factory = _merge_default_args(default, default_factory)
        self._ignore = ignore
        self._get = get
        self._dynamic = dynamic

    def __set_name__(self, cls, name):
        self._name = name

    def __get__(self, obj, cls=None):
        return self._load_value(obj)

    def __set__(self, obj, value):
        state = self._load_state(obj)
        state.setattr_value = value

    def __delete__(self, obj):
        state = self._load_state(obj)
        state.setattr_value = UNSPECIFIED

    def __call__(self, get):
        self._get = get
        return self

    def _override(self, args, kwargs, skip=frozenset()):
        # Make sure the override arguments match the constructor:
        import inspect
        sig = inspect.signature(self.__init__)
        sig.bind(*args, **kwargs)

        # Override the attributes referenced by the arguments:
        if args:
            self._keys = args

        if 'default' in kwargs or 'default_factory' in kwargs:
            self._default_factory = _merge_default_args(
                    kwargs.pop('default', UNSPECIFIED),
                    kwargs.pop('default_factory', UNSPECIFIED),
            )

        for key in kwargs.copy():
            if key not in skip:
                setattr(self, f'_{key}', kwargs.pop(key))

    def _load_state(self, obj):
        model.init(obj)
        states = model.get_param_states(obj)

        if self._name not in states:
            default = self._default_factory()
            states[self._name] = self._State(default)

        return states[self._name]

    def _load_value(self, obj):
        state = self._load_state(obj)

        if state.setattr_value is not UNSPECIFIED and (
                self._ignore is UNSPECIFIED or 
                state.setattr_value != self._ignore
        ):
            value = state.setattr_value

        else:
            model_version = model.get_cache_version(obj)
            is_cache_stale = (
                    state.cache_version != model_version or
                    self._dynamic
            )
            if is_cache_stale:
                state.cache_value = self._calc_value(obj)
                state.cache_version = model_version

            value = state.cache_value

        return self._get(obj, value)

    def _load_bound_keys(self, obj):
        state = self._load_state(obj)
        model_version = model.get_cache_version(obj)
        if state.cache_version != model_version:
            state.bound_keys = self._calc_bound_keys(obj)
        return state.bound_keys

    def _load_default(self, obj):
        return self._load_state(obj).default_value

    def _calc_value(self, obj):
        with AppcliError.add_info(
                "getting '{param}' parameter for {obj!r}",
                obj=obj,
                param=self._name,
        ):
            bound_keys = self._load_bound_keys(obj)
            default = self._load_default(obj)
            values = model.iter_values(obj, bound_keys, default)
            return self._pick(values)

    def _calc_bound_keys(self, obj):
        from appcli import Config
        from inspect import isclass

        keys = [
                Key(x) if isclass(x) and issubclass(x, Config) else x
                for x in self._keys or [self._name]
        ]
        bound_configs = model.get_bound_configs(obj)
        are_key_objs = [isinstance(x, Key) for x in keys]

        if all(are_key_objs):
            return [
                    model.BoundKey(
                        bound_config,
                        key.key or self._name,
                        key.cast or self._cast,
                    )
                    for key in keys
                    for bound_config in bound_configs
                    if isinstance(bound_config.config, key.config_cls)
            ]

        if any(are_key_objs):
            err = ConfigError(
                    keys=keys,
            )
            err.brief = "can't mix regular keys (e.g. strings) with Key objects"
            err.info = lambda e: '\n'.join((
                    "keys:",
                    *map(repr, e['keys']),
            ))
            raise err

        if len(keys) == 1:
            return [
                    model.BoundKey(bound_config, keys[0], self._cast)
                    for bound_config in bound_configs
            ]

        if len(keys) != len(bound_configs):
            err = ConfigError(
                    configs=[x.config for x in bound_configs],
                    keys=keys,
            )
            err.brief = "number of keys must match the number of configs"
            err.info += lambda e: '\n'.join((
                    f"configs ({len(e.configs)}):",
                    *map(repr, e.configs),
            ))
            err.blame += lambda e: '\n'.join((
                    f"keys ({len(e['keys'])}):",
                    *map(repr, e['keys']),
            ))
            return err

        return [
                model.BoundKey(bound_config, key, self._cast)
                for bound_config, key in zip(bound_configs, keys)
        ]

class Key:

    def __init__(self, config_cls, key=None, *, cast=None):
        self.config_cls = config_cls
        self.key = key
        self.cast = cast

    def __repr__(self):
        return f'appcli.Key({self.config_cls.__name__}, {self.key!r}, cast={self.cast!r})'

def _merge_default_args(instance, factory):
    have_instance = instance is not UNSPECIFIED
    have_factory = factory is not UNSPECIFIED

    if have_instance and have_factory:
        err = ScriptError(
                instance=instance,
                factory=factory,
        )
        err.brief = "can't specify 'default' and 'default_factory'"
        err.info += "default: {instance}"
        err.info += "default_factory: {factory}"
        raise err

    if have_factory:
        return factory
    else:
        return lambda: instance

