#!/usr/bin/env python3

def on_load(f):
    if isinstance(f, type):
        return lambda g: OnLoad(g, f)
    else:
        return OnLoad(f)

class OnLoad:

    def __init__(self, callback, config_cls=None):
        self.callback = callback
        self.config_cls = config_cls

    def __get__(self, obj, cls=None):
        return self.callback.__get__(obj, cls)

    def __call__(self, obj):
        self.callback(obj)

    def is_relevant(self, updated_configs):
        if self.config_cls is None:
            return bool(updated_configs)
        else:
            return any(
                    isinstance(x, self.config_cls)
                    for x in updated_configs
            )




