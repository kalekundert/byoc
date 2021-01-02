#!/usr/bin/env python3

from . import model
from .errors import AppcliError, ConfigError, ScriptError
from .model import SENTINEL
from more_itertools import first, zip_equal, UnequalIterablesError
from collections.abc import Mapping, Iterable

# Caching
# =======
# - If load() called, recalculate
# - If any configs/layers request it, recalculate
#   - configs, or layers...
#   - want to ignore configs that haven't been loaded yet; using layers is a 
#     natural way to do that.
#   - but if I'm going to iterate through each layer anyways, I might as well 
#     just look up the value.
#   - If looking up the value is expensive, the config can be responsible for 
#     caching.
#
# 2020/12/24:
# - Always cache values after load:
#   - obj.meta.load_count / load_id / cache_id / cache_version
#   - param.load_count
#   - param.cached_value
#
#   - in param.__get__():
#       # way to tell if this param is stale
#       if obj.load_count == self.load_count:
#           return self.cached_value
#
#       else:
#           ...
#           self.load_count = obj.load_count
#
# - give param() a `dynamic` attribute that causes it to recalculate its 
#   attribute each time.
#       

# Not natural to get multiple values from a single param.

# Would be nice to have way to get same parameter from two different keys.
#
# appcli.param()\
#       .key(DocoptConfig, '--flag',     cast=lambda x: x)\
#       .key(DocoptConfig, '--not-flag', cast=lambda x: not x)
#
# keys/casts specified as:
# - scalar
# - map
# - list
# - list of tuples
#
# map data structure:
# - dict
#   - key: Config object
#   - value: list of key, cast pairs
#

class param:

    def __init__(self, *keys, key=SENTINEL, default=SENTINEL, ignore=SENTINEL, cast=lambda x: x, pick=first):
        if keys and key is not SENTINEL:
            err = ScriptError(
                    implicit=keys,
                    explicit=key,
            )
            err.brief = "can't specify keys twice"
            err.info += lambda e: f"first specification:  {', '.join(repr(x) for x in e.implicit)}"
            err.info += lambda e: f"second specification: {e.explicit!r}"
            raise err

        if keys:
            self.keys = list(keys)
        else:
            self.keys = key if key is not SENTINEL else {}

        self.value = SENTINEL
        self.default = default
        self.ignore = ignore
        self.cast = cast
        self.pick = pick

    def __set_name__(self, cls, name):
        self.name = name

    def __get__(self, obj, cls=None):
        model.init(obj)

        try:
            return model.get_overrides(obj)[self.name]
        except KeyError:
            pass

        with AppcliError.add_info(
                "getting '{param}' parameter for {obj!r}",
                obj=obj,
                param=self.name,
        ):
            values = model.iter_values(
                    obj,
                    key_map=self.make_key_map(obj),
                    cast_map=self.make_cast_map(obj),
                    default=self.default,
            )
            return self.pick(values)

    def __set__(self, obj, value):
        if value != self.ignore:
            model.init(obj)
            model.get_overrides(obj)[self.name] = value

    def __delete__(self, obj):
        model.init(obj)
        del model.get_overrides(obj)[self.name]

    def make_key_map(self, obj):

        def sequence_len_err(configs, values):
            err = ConfigError(
                configs=configs,
                keys=values,
            )
            err.brief = "number of keys must match the number of configs"
            err.info += lambda e: '\n'.join(
                    f"{len(e.groups)} configs:",
                    *map(repr, e.groups),
            )
            err.blame += lambda e: '\n'.join(
                    f"{len(e['keys'])} keys:",
                    *map(repr, e['keys']),
            )
            return err

        return make_map(
                configs=model.get_configs(obj),
                values=self.keys or self.name,
                sequence_len_err=sequence_len_err,
        )

    def make_cast_map(self, obj):

        def sequence_len_err(configs, values):
            err = ConfigError(
                configs=configs,
                functions=values,
            )
            err.brief = "number of cast functions must match the number of configs"
            err.info += lambda e: '\n'.join(
                    f"{len(e.groups)} configs:",
                    *map(repr, e.groups),
            )
            err.blame += lambda e: '\n'.join((
                    f"{len(e.functions)} functions:",
                    *map(repr, e.functions),
            ))
            return err

        return make_map(
                configs=model.get_configs(obj),
                values=self.cast,
                sequence_len_err=sequence_len_err,
        )


def make_map(configs, values, unused_keys_err=ValueError, sequence_len_err=ValueError):
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

