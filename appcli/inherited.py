#!/usr/bin/env python3

from copy import copy

class inherited_param:

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def __set_name__(self, cls, name):
        for super_cls in cls.__mro__[1:]:
            try:
                parent = super_cls.__dict__[name]
                break
            except KeyError:
                pass
        else:
            err = ScriptError(
                    cls=cls,
                    name=name,
            )
            err.brief = "no superclass parameter to inherit from"
            err.info += "attempting to create `inherited_param`:\n{cls.__name__}.{name}"
            err.blame += lambda e: "\n".join(
                    "none of the following exist:", *(
                        f'{x.__qualname__}.{e.name}'
                        for x in e.cls.__mro__[1:]
                    )
            )
            raise err

        param = copy(parent)
        param._override(self._args, self._kwargs)

        setattr(cls, name, param)

