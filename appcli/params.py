#!/usr/bin/env python3

from . import model
from .errors import AppcliError, ConfigError, ScriptError
from .model import SENTINEL
from .utils import noop
from more_itertools import first, zip_equal, UnequalIterablesError
from collections.abc import Mapping, Iterable, Sequence

class param:

    class _State:

        def __init__(self):
            self.setattr_value = SENTINEL
            self.cache_value = SENTINEL
            self.cache_version = -1

    def __init__(self,
            *key_args,
            key=None,
            default=SENTINEL,
            ignore=SENTINEL,
            cast=None,
            pick=first,
            get=lambda obj, x: x,
            set=lambda obj: None,
            dynamic=False,
    ):
        if key_args and key is not None:
            err = ScriptError(
                    implicit=key_args,
                    explicit=key,
            )
            err.brief = "can't specify keys twice"
            err.info += lambda e: f"first specification:  {', '.join(repr(x) for x in e.implicit)}"
            err.info += lambda e: f"second specification: {e.explicit!r}"
            raise err

        self._keys = list(key_args) if key_args else key
        self._default = default
        self._ignore = {SENTINEL, ignore}
        self._cast = cast
        self._pick = pick
        self._get = get
        self._set = set
        self._dynamic = dynamic

    def __set_name__(self, cls, name):
        self._name = name

    def __get__(self, obj, cls=None):
        self._init_obj(obj)
        state = model.get_param_state(obj, self._name)

        if state.setattr_value not in self._ignore:
            return state.setattr_value

        model_version = model.get_cache_version(obj)
        is_cache_stale = (
                state.cache_version != model_version or
                self._dynamic
        )
        if is_cache_stale:
            state.cache_value = self._calc_value(obj)
            state.cache_version = model_version

        return state.cache_value

    def __set__(self, obj, value):
        self._init_obj(obj)
        state = model.get_param_state(obj, self._name)
        state.setattr_value = value

    def __delete__(self, obj):
        self._init_obj(obj)
        state = model.get_param_state(obj, self._name)
        state.setattr_value = SENTINEL

    def _init_obj(self, obj):
        model.init(obj)
        model.init_param_state(obj, self._name, self._State())

    def _calc_value(self, obj):
        with AppcliError.add_info(
                "getting '{param}' parameter for {obj!r}",
                obj=obj,
                param=self._name,
        ):
            key_map = self._calc_key_map(obj)
            values = model.iter_values(obj, key_map, self._default)
            return self._pick(values)

    def _calc_key_map(self, obj):
        configs = model.get_configs(obj)

        if _is_key_list(self._keys):
            if self._cast:
                raise ScriptError(
                        "can't specify both key=[appcli.Key] and cast=...; ambiguous",
                        keys=self._keys,
                        cast=self._cast,
                )

            return _key_map_from_key_list(
                    configs,
                    self._keys,
            )

        else:
            return _key_map_from_dict_equivs(
                    configs,
                    self._keys or self._name,
                    self._cast,
            )


class Key:

    def __init__(self, config_cls, key, *, cast=noop):
        self.config_cls = config_cls
        self.key = key
        self.cast = cast

    def __repr__(self):
        return f'appcli.Key({self.config_cls!r}, {self.key!r}, cast={self.cast!r})'

    @property
    def tuple(self):
        return self.key, self.cast

def _is_key_list(x):
    return bool(x) and isinstance(x, Sequence) and \
            all(isinstance(xi, Key) for xi in x)

def _key_map_from_key_list(configs, keys):
    map = {}

    for config in configs:
        for key in keys:
            if isinstance(config, key.config_cls):
                map.setdefault(config, []).append(key.tuple)

    return map

def _key_map_from_dict_equivs(configs, keys, casts=None):
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
            casts or noop,
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

