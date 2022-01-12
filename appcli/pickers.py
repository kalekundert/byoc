#!/usr/bin/env python3

from .model import UNSPECIFIED
from .errors import NoValueFound

class ValuesIter:
    # In the future, I might also teach this class to somehow indicate where 
    # each value was loaded from.

    def __init__(self, getters, default, log):
        self.getters = getters
        self.default = default
        self.log = log

    def __iter__(self):
        have_value = False

        if not self.getters:
            self.log.info("nowhere to look for values")

        for getter in self.getters:
            for value in getter.iter_values(self.log):
                have_value = True
                yield getter.cast_value(value)

        if self.default is not UNSPECIFIED:
            have_value = True
            self.log.info("got default value: {default!r}", default=self.default)
            yield self.default

        if not have_value:
            self.log.hint("did you mean to provide a default?")

def first(values):
    try:
        return next(iter(values))
    except StopIteration as err:
        raise NoValueFound("can't find value for parameter", values.log)


