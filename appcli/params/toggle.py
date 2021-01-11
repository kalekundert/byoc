#!/usr/bin/env python3

from more_itertools import partition, first
from .. import model
from .param import param, UNSPECIFIED, _dict_from_equiv
from ..errors import ConfigError

class Toggle:

    def __init__(self, value):
        self.value = value

def pick_toggled(values):
    values, toggles = partition(
            lambda x: isinstance(x, Toggle),
            values,
    )

    toggle = first(toggles, Toggle(False))

    try:
        value = first(values)
    except ValueError:
        err = ConfigError()
        err.brief = "can't find base value to toggle"
        err.hints += "did you mean to specify a default?"
        raise err

    return toggle.value != value

class toggle_param(param):
    # This class is somewhat limited in that it doesn't provide a way to 
    # specify toggle and non-toggle keys from the same config.  If this feature 
    # is needed, use `param` with `Toggle` and `pick_toggled()`.  This class is 
    # meant to be syntactic sugar, so I consider it acceptable that it doesn't 
    # cover all use cases.  Plus, it's hard to think of an example where having 
    # toggle and non-toggle keys in the same config would make sense.

    def __init__(
            self,
            *key_args,
            key=None,
            cast=None,
            toggle=None,
            default=UNSPECIFIED,
            ignore=UNSPECIFIED,
            get=lambda obj, x: x,
            dynamic=False,
    ):
        super().__init__(
            *key_args,
            key=key,
            cast=cast,
            pick=pick_toggled,
            default=default,
            ignore=ignore,
            get=get,
            dynamic=dynamic,
        )
        self._toggle = toggle

    def _calc_key_map(self, obj):
        key_map = super()._calc_key_map(obj)

        for config in key_map:
            if any((isinstance(config, x) for x in self._toggle)):
                key_map[config] = [
                        (key, lambda x: Toggle(cast(x)))
                        for key, cast in key_map[config]
                ]

        return key_map
