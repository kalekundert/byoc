#!/usr/bin/env python3

from .model import UNSPECIFIED
from .meta import UnknownMeta, DefaultMeta
from .errors import NoValueFound
from typing import Iterable
from funcy import autocurry

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
            self.log += "nowhere to look for values"

        for getter in self.getters:
            for value, meta, dynamic in getter.iter_values(self.log):
                have_value = True
                self.dynamic = self.dynamic or dynamic
                yield getter.cast_value(value, meta), meta

        if self.default is not UNSPECIFIED:
            have_value = True
            self.log += lambda: f"got default value: {self.default!r}"
            yield self.default, DefaultMeta()

        if not have_value:
            self.log += "did you mean to provide a default?"

def first(it: Iterable):
    try:
        value, meta = next(iter(it.with_meta))
        it.meta = meta
        return value
    except StopIteration as err:
        raise NoValueFound("can't find value for parameter", it.log) from None

def list(it: Iterable):
    from builtins import list

    items = list(zip(*it.with_meta))

    if items:
        values, metas = map(list, items)
    else:
        values, metas = [], []

    it.meta = metas
    return values

@autocurry
def merge_dicts(it: Iterable, keep_last=False):
    values = {}
    it.meta = {}

    for dict_, meta in it.with_meta:
        for key, value in dict_.items():
            if (key not in values) or keep_last:
                values[key] = value
                it.meta[key] = meta

    return values



