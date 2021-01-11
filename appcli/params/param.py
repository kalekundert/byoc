#!/usr/bin/env python3

from .. import model
from ..errors import AppcliError, ConfigError, ScriptError
from ..model import UNSPECIFIED
from ..utils import noop
from more_itertools import first, zip_equal, UnequalIterablesError
from collections.abc import Mapping, Iterable, Sequence

class param:

    class _State:

        def __init__(self, default):
            self.key_map = None
            self.setattr_value = UNSPECIFIED
            self.cache_value = UNSPECIFIED
            self.cache_version = -1
            self.default_value = default

    def __init__(
            self,
            *key_args,
            key=None,
            cast=None,
            pick=first,
            default=UNSPECIFIED,
            default_factory=UNSPECIFIED,
            ignore=UNSPECIFIED,
            get=lambda obj, x: x,
            dynamic=False,
    ):
        self._keys = _merge_key_args(key_args, key)
        self._cast = cast
        self._pick = pick
        self._default_factory = _merge_default_args(default, default_factory)
        self._ignore = ignore
        self._get = get
        self._dynamic = dynamic

    def __set_name__(self, cls, name):
        self._name = name

    def __get__(self, obj, cls=None):
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
        if args or 'key' in kwargs:
            self._keys = _merge_key_args(args, kwargs.pop('key', None))

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

    def _load_key_map(self, obj):
        state = self._load_state(obj)
        if state.key_map is None:
            state.key_map = self._calc_key_map(obj)
        return state.key_map

    def _load_default(self, obj):
        return self._load_state(obj).default_value

    def _calc_value(self, obj):
        with AppcliError.add_info(
                "getting '{param}' parameter for {obj!r}",
                obj=obj,
                param=self._name,
        ):
            key_map = self._load_key_map(obj)
            default = self._load_default(obj)
            values = model.iter_values(obj, key_map, default)
            return self._pick(values)

    def _calc_key_map(self, obj):
        configs = model.get_configs(obj)

        if _is_key_list(self._keys):
            return _key_map_from_key_list(
                    configs,
                    self._keys,
                    self._cast or noop,
            )

        else:
            return _key_map_from_dict_equivs(
                    configs,
                    self._keys or self._name,
                    self._cast or noop,
            )

class Key:

    def __init__(self, config_cls, key, *, cast=None):
        self.config_cls = config_cls
        self.key = key
        self.cast = cast

    def __repr__(self):
        return f'appcli.Key({self.config_cls.__name__}, {self.key!r}, cast={self.cast!r})'

    @property
    def tuple(self):
        return self.key, self.cast

def _merge_key_args(implicit, explicit):
    if implicit and explicit is not None:
        err = ScriptError(
                implicit=implicit,
                explicit=explicit,
        )
        err.brief = "can't specify keys twice"
        err.info += lambda e: f"first specification:  {', '.join(repr(x) for x in e.implicit)}"
        err.info += lambda e: f"second specification: {e.explicit!r}"
        raise err

    return list(implicit) if implicit else explicit

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

def _is_key_list(x):
    return bool(x) and isinstance(x, Sequence) and \
            all(isinstance(xi, Key) for xi in x)

def _key_map_from_key_list(configs, keys, default_cast):
    if not callable(default_cast):
        err = ScriptError(
                keys=keys,
                cast=default_cast,
        )
        err.brief = "cast=... must be callable when specified with key=[appcli.Key]"
        err.info += lambda e: '\n'.join(("keys:", *map(repr, e['keys'])))
        err.blame += "cast:\n{cast}"
        raise err

    key_map = {}

    for config in configs:
        for key in keys:
            if isinstance(config, key.config_cls):
                item = key.key, key.cast or default_cast
                key_map.setdefault(config, []).append(item)

    return key_map

def _key_map_from_dict_equivs(configs, keys, casts):
    def unused_keys_err(value_type):

        def err_factory(configs, values, unused_keys):
            err = ConfigError(
                    value_type=value_type,
                    configs=configs,
                    values=values,
                    unused_keys=unused_keys,
            )
            err.brief = "given {value_type} that don't correspond to any config"
            err.info += lambda e: '\n'.join((
                    f"configs:",
                    *map(repr, e.configs),
            ))
            err.info += lambda e: '\n'.join((
                    f"unused {value_type}:", *(
                        f"{k!r}: {e['values'][k]}" for k in e.unused_keys
                    )
            ))
            return err

        return err_factory

    def sequence_len_err(value_type):

        def err_factory(configs, values):
            err = ConfigError(
                    value_type=value_type,
                    configs=configs,
                    values=values,
            )
            err.brief = "number of {value_type} must match the number of configs"
            err.info += lambda e: '\n'.join((
                    f"configs ({len(e.configs)}):",
                    *map(repr, e.configs),
            ))
            err.blame += lambda e: '\n'.join((
                    f"{value_type} ({len(e['values'])}):",
                    *map(repr, e['values']),
            ))
            return err

        return err_factory

    key_map = _dict_from_equiv(
            configs,
            keys,
            unused_keys_err=unused_keys_err('keys'),
            sequence_len_err=sequence_len_err('keys'),
    )
    cast_map = _dict_from_equiv(
            configs,
            casts,
            unused_keys_err=unused_keys_err('cast functions'),
            sequence_len_err=sequence_len_err('cast functions'),
    )

    return {
            k: [(v, cast_map.get(k, noop))]
            for k, v in key_map.items()
    }

def _dict_from_equiv(configs, values, unused_keys_err=ValueError, sequence_len_err=ValueError):
    # If the values are given as a dictionary, use the keys to identify the 
    # most appropriate value for each config.
    if isinstance(values, Mapping):
        result = {}
        unused_keys = set(values.keys())

        def rank_values(config, values):
            for key, value in values.items():
                try:
                    yield config.__class__.__mro__.index(key), key, value
                except ValueError:
                    continue

        for config in configs:
            ranks = sorted(rank_values(config, values))
            if not ranks:
                continue

            i, key, value = ranks[0]
            unused_keys.discard(key)

            result[config] = value

        if unused_keys:
            raise unused_keys_err(configs, values, unused_keys)

        return result

    # If the values are given as a sequence, make sure there is a value for 
    # each config, then match them to each other in order.
    if isinstance(values, Iterable) and not isinstance(values, str):
        configs, values = list(configs), list(values)
        try:
            pairs = zip_equal(configs, values)
            return {k: v for k, v in pairs if v is not ...}
        except UnequalIterablesError:
            raise sequence_len_err(configs, values) from None

    # If neither of the above applies, interpret the given value as a scalar 
    # meant to be applied to every config:
    return {k: values for k in configs}

