#!/usr/bin/env python3

from . import model
from .utils import lookup
from .errors import AppcliError, ConfigError, ScriptError
from more_itertools import first, zip_equal, UnequalIterablesError
from collections.abc import Mapping, Iterable

SENTINEL = object()

class param:

    def __init__(self, *keys, key=SENTINEL, default=SENTINEL, cast=lambda x: x, pick=first):
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

        layers = model.get_layers(obj)
        key_map = self.make_key_map(obj)
        cast_map = self.make_cast_map(obj)

        with AppcliError.add_info(
                "getting '{attr}' parameter for {obj!r}",
                obj=obj,
                attr=self.name,
        ):
            values = iter_values_from_layers(
                    layers=layers,
                    key_map=key_map,
                    cast_map=cast_map,
                    default=self.default,
            )
            return self.pick(values)

    def __set__(self, obj, value):
        model.init(obj)
        model.get_overrides(obj)[self.name] = value

    def __delete__(self, obj):
        model.init(obj)
        del model.get_overrides(obj)[self.name]

    def make_key_map(self, obj):

        def sequence_len_err(keys, values):
            err = ConfigError(
                keys=values,
                groups=keys,
            )
            err.brief = "number of keys must match the number of key groups"
            err.info += lambda e: f"{len(e.groups)} groups: {', '.join(e.groups)}"
            err.error += lambda e: f"{len(e.functions)} keys: {', '.join(e.keys)}"
            return err

        return make_map(
                keys=model.get_key_groups(obj),
                values=self.keys,
                default=self.name,
                sequence_len_err=sequence_len_err,
        )

    def make_cast_map(self, obj):

        def sequence_len_err(keys, values):
            err = ConfigError(
                functions=values,
                groups=keys,
            )
            err.brief = "number of cast functions must match the number of cast groups"
            err.info += lambda e: f"{len(e.groups)} groups: {', '.join(e.groups)}"
            err.error += lambda e: f"{len(e.functions)} functions: {', '.join(e.functions)}"
            return err

        return make_map(
                keys=model.get_cast_groups(obj),
                values=self.cast,
                default=lambda x: x,
                sequence_len_err=sequence_len_err,
        )

def iter_values_from_layers(layers, key_map, cast_map, default=SENTINEL):
    lookups = []
    have_value = False

    for layer in layers:
        key = key_map[layer.config.key_group]
        cast = cast_map[layer.config.cast_group]
        lookups.append((key, layer.location))

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
                err2.info += "reading {key!r} from {location}"
                err2.blame += str(err1)
                raise err2 from err1
            else:
                have_value = True

    if default is not SENTINEL:
        have_value = True
        yield default

    if not have_value:
        err = ConfigError(
                "parameter must have a value",
                lookups=lookups,
        )
        if not lookups:
            err.blame += "nowhere to look for values"
            err.hints += f"is `{model.CONFIG_ATTR}` empty?"
        else:
            err.info += lambda e: "\n    ".join([
                    "the following locations were searched:", *(
                        f'{loc}: {key}'
                        for key, loc in e.lookups
                    )
            ])
            err.hints += "did you mean to provide a default?"
        raise err from None

def make_map(keys, values, default=SENTINEL, missing_key_err=ValueError, sequence_len_err=ValueError):
    """
    Create a dictionary from the given keys and values.
    """

    # If the values are given as a mapping, either fill in or complain about 
    # any missing keys, depending on whether or not a default is given.
    if isinstance(values, Mapping):
        keys = set(keys)

        if default is not SENTINEL:
            return {k: values.get(k, default) for k in keys}

        else:
            try:
                return {k: values[k] for k in keys}
            except KeyError:
                missing_keys = keys - set(values.keys())
                raise missing_key_err(keys, values, missing_keys) from None

    # If the values are given as a sequence, make sure there is a key for each 
    # value, then match them to each other in order.
    if isinstance(values, Iterable) and not isinstance(values, str):
        keys, values = list(keys), list(values)
        try:
            return dict(zip_equal(keys, values))
        except UnequalIterablesError:
            raise sequence_len_err(keys, values) from None

    # If neither of the above applies, interpret the given value as a scalar 
    # meant to be applied to every key:
    return {k: values for k in keys}


