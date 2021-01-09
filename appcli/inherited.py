#!/usr/bin/env python3

from .params import param, _merge_key_args

# Create a new sentinel for use only in this module.
_SENTINEL = object()

class inherited_param(param):
    # This class isn't compatible with toggle_param, but I'm not sure the best 
    # way to do that.  I'd probably have to use __set_name__ to replace this 
    # object with a copy of the parent class descriptor.  The part I can't 
    # figure out is how to support the fact that arbitrary `param` classes 
    # could have arbitrary attributes.  Maybe I need to

    # init: needs to get all kwargs
    # __set_name__:
    # - copy param
    # - call param._override(kwargs)
    #
    # param._override:
    # - make sure arguments match construtor (inspect)
    # - handle keys, pop from dictionary
    #   - subclasses can call, then deal with remaining

    def __init__(
            self,
            *key_args,
            key=_SENTINEL,
            cast=_SENTINEL,
            pick=_SENTINEL,
            default=_SENTINEL,
            ignore=_SENTINEL,
            get=_SENTINEL,
            set=_SENTINEL,
            dynamic=_SENTINEL,
    ):

        if key_args or key is not _SENTINEL:
            keys = _merge_key_args(
                    key_args,
                    key if key is not _SENTINEL else None,
            )
        else:
            keys = _SENTINEL

        self._overrides = {
                '_keys': keys,
                '_cast': cast,
                '_pick': pick,
                '_default': default,
                '_ignore': ignore,
                '_get': get,
                '_set': set,
                '_dynamic': dynamic,
        }

    def __set_name__(self, cls, name):
        super().__set_name__(cls, name)

        # Find the superclass parameter to inherit from:

        for super_cls in cls.__mro__[1:]:
            try:
                parent = super_cls.__dict__[name]
                break
            except KeyError:
                pass
        else:
            raise ScriptError

        # Configure this parameter:

        for attr, x in self._overrides.items():
            x = x if x is not _SENTINEL else getattr(parent, attr)
            setattr(self, attr, x)

        del self._overrides

