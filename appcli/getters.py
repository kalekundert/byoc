#!/usr/bin/env python3

from . import model
from .utils import lookup
from .errors import ConfigError
from more_itertools import always_iterable
from inform import did_you_mean

class Getter:

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __repr__(self):
        cls = f'appcli.{self.__class__.__name__}'
        args = self.__reprargs__()
        kwargs = [f'{k}={v!r}' for k, v in self.kwargs.items()]
        return f'{cls}({", ".join((*args, *kwargs))})'

    def __reprargs__(self):
        return []

    def bind(self, obj, param):
        given_kwargs = set(self.kwargs.keys())
        known_kwargs = param._get_known_getter_kwargs()
        unknown_kwargs = given_kwargs - known_kwargs

        if unknown_kwargs:
            err = ConfigError(
                    getter=self,
                    obj=obj,
                    param=param,
                    given_kwargs=given_kwargs,
                    known_kwargs=known_kwargs,
                    unknown_kwargs=unknown_kwargs,
            )
            err.brief = f'unexpected keyword argument'
            err.info += lambda e: '\n'.join([
                f"{e.param.__class__.__name__}() allows the following kwargs:",
                *e.known_kwargs,
            ])
            err.blame += lambda e: '\n'.join([
                f"{e.getter!r} has the following unexpected kwargs:",
                *e.unknown_kwargs,
            ])
            raise err

        # This attribute is public and can be modified externally, e.g. by 
        # classes like `toggle_param()`.  This should be done with care, 
        # though, because the any modifications will need to be re-applied each 
        # time the cache expires.
        self.cast_funcs = list(always_iterable(
            self.kwargs.get('cast', []) or param._get_default_cast()
        ))

    def iter_values(self, locations):
        raise NotImplementedError

    def cast_value(self, x):
        for f in self.cast_funcs:
            try:
                x = f(x)
            except Exception as err1:
                err2 = ConfigError(
                        value=x,
                        function=f,
                )
                err2.brief = "can't cast {value!r} using {function!r}"
                err2.blame += str(err1)
                raise err2 from err1

        return x

class BaseKey(Getter):

    def __init__(self, key, **kwargs):
        super().__init__(**kwargs)
        self.key = key
        self.bound_configs = None

    def bind(self, obj, param):
        super().bind(obj, param)
        self.key = self.key or param._get_default_key()

    def iter_values(self, configs, locations):
        assert self.key is not None
        assert self.bound_configs is not None

        for bound_config in self.bound_configs:
            configs.append(bound_config.config)

            for layer in bound_config:
                locations.append((layer.location, self.key))

                try:
                    value = lookup(layer.values, self.key)
                except KeyError:
                    continue

                with ConfigError.add_info(
                        "read {key!r} from {location}",
                        key=self.key,
                        location=layer.location,
                ):
                    yield value

class Key(BaseKey):

    def __init__(self, config_cls, key=None, **kwargs):
        super().__init__(key, **kwargs)
        self.config_cls = config_cls

    def __reprargs__(self):
        if self.key:
            return [self.config_cls.__name__, repr(self.key)]
        else:
            return [self.config_cls.__name__]

    def bind(self, obj, param):
        super().bind(obj, param)
        self.bound_configs = [
                bc for bc in model.get_bound_configs(obj)
                if isinstance(bc.config, self.config_cls)
        ]

class ImplicitKey(BaseKey):

    def __init__(self, key, bound_config):
        super().__init__(key)
        self.bound_configs = [bound_config]

    def __reprargs__(self):
        return [repr(self.key), repr(self.bound_configs)]

class Func(Getter):

    def __init__(self, callable, **kwargs):
        super().__init__(**kwargs)
        self.callable = callable
        self.args = ()
        self.kwargs = {}

    def __reprargs__(self):
        return [repr(self.callable)]

    def partial(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self

    def iter_values(self, configs, locations):
        yield self.callable(*self.args, **self.kwargs)

class Method(Func):

    def bind(self, obj, param):
        super().bind(obj, param)
        self.args = (obj, *self.args)

    def iter_values(self, configs, locations):
        # Methods used with this getter this will typically attempt to 
        # calculate a value based on other parameters.  An AttributeError will 
        # be raised if any of those parameters is missing a value.  The most 
        # sensible thing to do when this happens is to silently skip this 
        # getter, allowing the parameter to continue searching other getters 
        # for a value.

        try:
            yield from super().iter_values(configs, locations)
        except AttributeError:
            pass

class Value(Getter):

    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def __reprargs__(self):
        return [repr(self.value)]

    def iter_values(self, configs, locations):
        yield self.value






