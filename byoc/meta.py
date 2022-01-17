#!/usr/bin/env python3

from .model import get_meta

class Meta:

    def __repr__(self):
        loc_str = '' if not self.location else f'location={self.location!r}'
        return f'{self.__class__.__name__}({loc_str})'

    @property
    def location(self):
        pass

class NeverAccessedMeta(Meta):
    pass

class SetAttrMeta(Meta):
    pass

class GetterMeta(Meta):

    def __init__(self, getter):
        self.getter = getter

class LayerMeta(GetterMeta):

    def __init__(self, getter, layer):
        super().__init__(getter)
        self.layer = layer

    @property
    def location(self):
        return self.layer.location

class DefaultMeta(Meta):
    pass

class ExceptionMeta(Meta):

    def __init__(self, exc):
        self.exc = exc

class UnknownMeta(Meta):
    pass



class meta_view:

    def __get__(self, obj, cls=None):
        return _meta_view(obj)

class _meta_view:
    # This class will never refresh the cache, so the results it returns may 
    # change if the value is accessed immediately afterwards.  For this reason, 
    # it is recommended to always access any parameters of interest before 
    # accessing the metadata associated with those parameters.

    def __init__(self, obj):
        self.__obj = obj

    def __getattr__(self, param):
        return get_meta(self.__obj, param)

