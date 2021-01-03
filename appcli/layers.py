#!/usr/bin/env python3

import functools

class LayerGroup:

    def __init__(self, config):
        self.config = config
        self.layers = []
        self.is_loaded = False

    def __iter__(self):
        yield from self.layers

    def load(self, obj):
        self.layers = list(self.config.load(obj))
        for layer in self.layers:
            layer.config = self.config
        self.is_loaded = True

class Layer:

    def __init__(self, *, values, location):
        # Values: any object that:
        # - implements __getitem__ to either return value associated with Key, 
        #   or raise KeyError
        # - is a callable that takes a key as the only argument, and raises 
        #   KeyError if not found
        self.config = None
        self.values = values
        self.location = location

    def __repr__(self):
        return f'Layer(values={self.values!r}, location={self.location!r})'


def not_found(*raises):
    """
    Wrap the given function so that a KeyError is raised if any of the expected 
    kinds of exceptions are caught.

    This is meant to help implement the interface expected by `Layers.values`, 
    i.e. a callable that raises a KeyError if a value could not successfully be 
    found.
    """

    def decorator(f):

        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except tuple(raises) as err:
                raise KeyError from err

        return wrapped
        
    return decorator

