#!/usr/bin/env python3

from . import model
from .meta import meta_view

class BareMeta(type):
    """
    A metaclass that allows a class to be instantiated either in the usual way, 
    or without calling the constructor.  The latter is useful if the object 
    will be initialized in another way, e.g. `byoc.param()` parameters that 
    read from the command line.
    """

    def from_bare(cls):
        self = super(cls, cls).__new__(cls)
        if hasattr(self, '__bareinit__'):
            self.__bareinit__()
        return self

    def __call__(cls, *args, **kwargs):
        self = cls.from_bare()
        self.__init__(*args, **kwargs)
        return self

class App(metaclass=BareMeta):
    meta = meta_view()

    def __bareinit__(self):
        pass

    @classmethod
    def entry_point(cls):
        app = cls.from_bare()
        app.main()

    def main(self):
        raise NotImplementedError

    def load(self, config_cls=None):
        model.load(self, config_cls)

    def reload(self, config_cls=None):
        model.reload(self, config_cls)


