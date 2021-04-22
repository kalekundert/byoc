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

    def __init__(
            self,
            *keys,
            cast=noop,
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

    def _calc_bound_getters(self, obj):
        bound_getters = super()._calc_bound_getters(obj)

        for bg in bound_getters:
            if bg.kwargs.get('toggle', False):
                bg.cast_funcs.append(Toggle)

        return bound_getters

    def _get_known_getter_kwargs(self):
        return super()._get_known_getter_kwargs() | {'toggle'}
