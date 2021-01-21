#!/usr/bin/env python3

class AppMeta(type):
    """
    A metaclass that allows a class to be instantiated either in the usual way, 
    or without calling the constructor.  The latter is useful if the object 
    will be initialized in another way, e.g. `appcli.param()` parameters that 
    read from the command line.
    """

    def from_params(cls):
        self = super(cls, cls).__new__(cls)
        if hasattr(self, '__bareinit__'):
            self.__bareinit__()
        return self

    def __call__(cls, *args, **kwargs):
        self = cls.from_params()
        self.__init__(*args, **kwargs)
        return self

class App(metaclass=AppMeta):
    pass



