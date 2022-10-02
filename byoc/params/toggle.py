#!/usr/bin/env python3

from .. import model
from .param import param, UNSPECIFIED
from ..utils import noop
from ..cast import Context, call_with_context
from ..errors import NoValueFound
from more_itertools import partition, first

class Toggle:

    def __init__(self, value):
        self.value = value

def pick_toggled(values):
    bases, toggles = partition(
            lambda x: isinstance(x, Toggle),
            values,
    )

    toggle = first(toggles, Toggle(False))

    try:
        base = first(bases)
    except ValueError:
        raise NoValueFound("can't find base value to toggle", values.log)

    return toggle.value != base

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
                bg.cast.funcs.append(Toggle)

        return bound_getters

    def _prepare_cast_funcs(self, cast):
        cast = super()._prepare_cast_funcs(cast)

        def maintain_toggle(f):

            # I'm not exactly sure what a monad is, but I think that `Context` 
            # and `Toggle` might both meet the definition.  If so, there may be 
            # a way to simplify this code.

            def wrapper(context: Context):
                if isinstance(context.value, Toggle):
                    context.value = context.value.value
                    result = call_with_context(f, context)
                    return Toggle(result)
                else:
                    return call_with_context(f, context)

            return wrapper

        cast.funcs = [maintain_toggle(f) for f in cast.funcs]
        return cast

    def _get_known_getter_kwargs(self):
        return super()._get_known_getter_kwargs() | {'toggle'}
