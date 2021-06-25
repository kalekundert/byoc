#!/usr/bin/env python3

from . import model
from .model import UNSPECIFIED
from .errors import ConfigError
from more_itertools import always_iterable
from inform import did_you_mean
from functools import partial

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
        raise NotImplementedError

class Key(Getter):

    def __init__(self, config_cls, key=UNSPECIFIED, **kwargs):
        super().__init__(**kwargs)
        self.config_cls = config_cls
        self.key = key

    def __reprargs__(self):
        if self.key is UNSPECIFIED:
            return [self.config_cls.__name__]
        else:
            return [self.config_cls.__name__, repr(self.key)]

    def bind(self, obj, param):
        wrapped_configs = [
                wc for wc in model.get_wrapped_configs(obj)
                if isinstance(wc.config, self.config_cls)
        ]
        return BoundKey(self, obj, param, wrapped_configs)

class ImplicitKey(Getter):

    def __init__(self, wrapped_config, key):
        super().__init__()
        self.key = key
        self.wrapped_config = wrapped_config

    def __reprargs__(self):
        return [repr(self.key), repr(self.wrapped_config)]

    def bind(self, obj, param):
        return BoundKey(self, obj, param, [self.wrapped_config])

class Func(Getter):

    def __init__(self, callable, *, skip=(), **kwargs):
        super().__init__(**kwargs)
        self.callable = callable
        self.skip = skip
        self.partial_args = ()
        self.partial_kwargs = {}

    def __reprargs__(self):
        return [repr(self.callable)]

    def partial(self, *args, **kwargs):
        self.partial_args = args
        self.partial_kwargs = kwargs
        return self

    def bind(self, obj, param):
        return BoundCallable(
                self, obj, param,
                self.callable,
                self.partial_args,
                self.partial_kwargs,
                tuple(always_iterable(self.skip)),
        )

class Method(Func):

    def bind(self, obj, param):
        # Methods used with this getter this will typically attempt to 
        # calculate a value based on other parameters.  An AttributeError will 
        # be raised if any of those parameters is missing a value.  The most 
        # sensible thing to do when this happens is to silently skip this 
        # getter, allowing the parameter to continue searching other getters 
        # for a value.

        bc = super().bind(obj, param)
        bc.partial_args = (obj, *bc.partial_args)
        bc.exceptions = (AttributeError, *bc.exceptions)
        return bc

class Value(Getter):

    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def __reprargs__(self):
        return [repr(self.value)]

    def bind(self, obj, param):
        return BoundValue(self, obj, param, self.value)



class BoundGetter:

    def __init__(self, parent, obj, param):
        self.parent = parent
        self.obj = obj
        self.param = param

        # The following attributes are public and may be accessed or modified 
        # by `param` subclasses (e.g. `toggle_param`).  Be careful when making 
        # modifications, though, because any modifications will need to be 
        # re-applied each time the cache expires (because the getters are 
        # re-bound when this happens).
        self.kwargs = parent.kwargs
        self.cast_funcs = list(always_iterable(
            self.kwargs.get('cast', []) or param._get_default_cast()
        ))

        self._check_kwargs()

    def _check_kwargs(self):
        given_kwargs = set(self.kwargs.keys())
        known_kwargs = self.param._get_known_getter_kwargs()
        unknown_kwargs = given_kwargs - known_kwargs

        if unknown_kwargs:
            err = ConfigError(
                    getter=self.parent,
                    obj=self.obj,
                    param=self.param,
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

    def iter_values(self, log):
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

class BoundKey(BoundGetter):

    def __init__(self, parent, obj, param, wrapped_configs):
        super().__init__(parent, obj, param)
        self.key = parent.key
        self.wrapped_configs = wrapped_configs

        if self.key is UNSPECIFIED:
            self.key = param._get_default_key()

    def iter_values(self, log):
        assert self.key is not UNSPECIFIED
        assert self.wrapped_configs is not None

        if not self.wrapped_configs:
            log.info("no configs of class {config_cls.__name__}", config_cls=self.parent.config_cls)

        for wrapped_config in self.wrapped_configs:

            if not wrapped_config.is_loaded:
                log.info("skipped {config}: not loaded", config=wrapped_config.config)
                log.hint("did you mean to call `appcli.load()`?")
                continue

            if not wrapped_config.layers:
                log.info("skipped {config}: loaded, but no layers", config=wrapped_config.config)
                continue

            log.info("queried {config}:", config=wrapped_config.config)

            for layer in wrapped_config:
                yield from layer.iter_values(self.key, log)


class BoundCallable(BoundGetter):

    def __init__(self, parent, obj, param, callable, args, kwargs, exc=()):
        super().__init__(parent, obj, param)
        self.callable = callable
        self.partial_args = args
        self.partial_kwargs = kwargs
        self.exceptions = exc

    def iter_values(self, log):
        try:
            value = self.callable(*self.partial_args, **self.partial_kwargs)
        except self.exceptions as err:
            log.info("called: {getter.callable}\nraised {err.__class__.__name__}: {err}", getter=self, err=err)
            pass
        else:
            log.info("called: {getter.callable}\nreturned: {value!r}", getter=self, value=value)
            yield value


class BoundValue(BoundGetter):

    def __init__(self, parent, obj, param, value):
        super().__init__(parent, obj, param)
        self.value = value

    def iter_values(self, log):
        log.info("got hard-coded value: {getter.value}", getter=self)
        yield self.value







