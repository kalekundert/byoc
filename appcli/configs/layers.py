#!/usr/bin/env python3

import functools
from inspect import isclass

class Layer:

    def __init__(self, *, values, location):
        # Values:
        # - object that implements `__getitem__()` to either return value 
        #   associated with key, or raise KeyError.
        # - callable that takes no arguments and returns an object matching the 
        #   above description.
        #
        # Location:
        # - string
        # - callable that takes no arguments and returns a string.
        self.config = None
        self.values = values
        self.location = location

    def __repr__(self):
        return f'Layer(values={self._values!r}, location={self._location!r})'

    @property
    def values(self):
        if self._are_values_deferred:
            self._values = self._values()
            self._are_values_deferred = False
        return self._values

    @values.setter
    def values(self, values):
        self._values = values
        self._are_values_deferred = callable(values)

    @property
    def location(self):
        if self._is_location_deferred:
            self._location = self._location()
            self._is_location_deferred = False
        return self._location

    @location.setter
    def location(self, loc):
        self._location = loc
        self._is_location_deferred = callable(loc)

def dict_like(*args):

    # I want this function to be usable as a decorator, but I also want to 
    # avoid exposing `__call__()` so that these objects don't look like 
    # deferred values to `Layer`.  These competing requirements necessitate an 
    # awkward layering of wrapper functions and classes.
    
    class dict_like:

        def __init__(self, f, *raises):
            self.f = f
            self.raises = raises

        def __getitem__(self, key):
            try:
                return self.f(key)
            except tuple(self.raises) as err:
                raise KeyError from err

    is_exception = lambda x: isclass(x) and issubclass(x, Exception)

    if not args:
        return lambda f: dict_like(f)

    elif is_exception(args[0]):
        return lambda f: dict_like(f, *args)

    else:
        return dict_like(*args)
