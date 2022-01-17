#!/usr/bin/env python3

from .model import UNSPECIFIED
from .meta import UnknownMeta, DefaultMeta
from .errors import NoValueFound

class ValuesIter:

    # In the future, I might also teach this class to somehow indicate where 
    # each value was loaded from.

    def __init__(self, getters, default, log):
        self.getters = getters
        self.default = default
        self.log = log

        # Output attributes:
        self.dynamic = False
        self.meta = UnknownMeta()  # meant to be set by picker.

    def __iter__(self):
        yield from (v for v, m in self.with_meta)

    @property
    def with_meta(self):
        have_value = False
        self.dynamic = False

        if not self.getters:
            self.log.info("nowhere to look for values")

        for getter in self.getters:
            for value, meta, dynamic in getter.iter_values(self.log):
                have_value = True
                self.dynamic = self.dynamic or dynamic
                yield getter.cast_value(value), meta

        if self.default is not UNSPECIFIED:
            have_value = True
            self.log.info("got default value: {default!r}", default=self.default)
            yield self.default, DefaultMeta()

        if not have_value:
            self.log.hint("did you mean to provide a default?")

def first(values):
    try:
        value, meta = next(iter(values.with_meta))
        values.meta = meta
        return value
    except StopIteration as err:
        raise NoValueFound("can't find value for parameter", values.log)

