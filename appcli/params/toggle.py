#!/usr/bin/env python3

from .. import model
from .param import param, UNSPECIFIED
from ..utils import noop
from ..errors import ConfigError
from more_itertools import partition, first

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
            *keys,
            cast=noop,
            toggle=None,
            default=UNSPECIFIED,
            ignore=UNSPECIFIED,
            get=lambda obj, x: x,
            dynamic=False,
    ):
        super().__init__(
            *keys,
            cast=cast,
            pick=pick_toggled,
            default=default,
            ignore=ignore,
            get=get,
            dynamic=dynamic,
        )
        self._toggle = toggle

    def _calc_bound_keys(self, obj):
        bound_keys = super()._calc_bound_keys(obj)

        for bound_key in bound_keys:
            config = bound_key.bound_config.config
            if any(isinstance(config, x) for x in self._toggle):
                cast = bound_key.cast
                bound_key.cast = lambda x: Toggle(cast(x))

        return bound_keys
