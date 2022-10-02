#!/usr/bin/env python3

import inspect
import functools

from .. import model
from ..model import UNSPECIFIED
from ..getters import Getter, Key, ImplicitKey
from ..pick import ValuesIter, first
from ..cast import CastFuncs
from ..meta import NeverAccessedMeta, ExceptionMeta, SetAttrMeta
from ..utils import noop
from ..errors import ApiError, NoValueFound, Log
from contextlib import contextmanager
from math import inf

class param:

    class _State:

        def __init__(self, default):
            self.default = default
            self.reset()

        def reset(self):
            self.value = UNSPECIFIED
            self.exception = UNSPECIFIED
            self.meta = NeverAccessedMeta()
            self.dynamic = False
            self.cache_version = -1

    def __init__(
            self,
            *keys,
            cast=noop,
            pick=first,
            default=UNSPECIFIED,
            default_factory=UNSPECIFIED,
            ignore=UNSPECIFIED,
            get=lambda obj, x: x,
            dynamic=False,
    ):
        self._keys = keys
        self._cast = self._prepare_cast_funcs(cast)
        self._pick = pick
        self._default_factory = _merge_default_args(default, default_factory)
        self._ignore = ignore
        self._get = get
        self._dynamic = dynamic

        for key in keys:
            if isinstance(key, Getter):
                key.register(self)

    def __set_name__(self, cls, name):
        self._name = name

    def __get__(self, obj, cls=None):
        return self._load_value(obj) if obj is not None else self

    def __set__(self, obj, value):
        if value is self._ignore:
            return

        state = self._load_state(obj)
        state.value = value
        state.exception = UNSPECIFIED
        state.meta = SetAttrMeta()
        state.dynamic = False
        state.cache_version = inf

    def __delete__(self, obj):
        state = self._load_state(obj)
        state.reset()

    def __call__(self, get):
        # Allow the descriptor to be used as a decorator.
        self._get = get
        return self

    def _override(self, args, kwargs, skip=frozenset()):
        # Make sure the override arguments match the constructor:
        sig = inspect.signature(self.__init__)
        sig.bind(*args, **kwargs)

        # Override the attributes referenced by the arguments:
        if args:
            self._keys = args

        if 'cast' in kwargs:
            self._cast = self._prepare_cast_funcs(kwargs.pop('cast'))

        if 'default' in kwargs or 'default_factory' in kwargs:
            self._default_factory = _merge_default_args(
                    kwargs.pop('default', UNSPECIFIED),
                    kwargs.pop('default_factory', UNSPECIFIED),
            )

        for key in kwargs.copy():
            if key not in skip:
                setattr(self, f'_{key}', kwargs.pop(key))

    def _load_state(self, obj):
        model.init(obj)
        states = model.get_param_states(obj)

        if self._name not in states:
            default = self._default_factory()
            states[self._name] = self._State(default)

        return states[self._name]

    def _load_value(self, obj, state=None):
        state = state or self._load_state(obj)

        self._update_value(obj, state)

        if state.exception is not UNSPECIFIED:
            raise state.exception

        return self._get(obj, state.value)

    def _update_value(self, obj, state=None, log=None):
        state = state or self._load_state(obj)

        model_version = model.get_cache_version(obj)
        is_cache_stale = (
                state.cache_version < model_version or
                state.dynamic or
                self._dynamic
        )
        if not is_cache_stale:
            return

        log = log or Log()

        # Previously, I used the object's normal repr in this message instead 
        # of explicitly deferring to a generic repr.  However, this led to 
        # infinite recursion in cases where a parameter didn't exist but the 
        # repr function tried to access it.  I tried to fix this by adding a 
        # try/except block, but that ended up triggering a core dump in 
        # python==3.8, see #41.  This was very likely due to a bug in python, 
        # but on the principle that logging code should "do no harm" above 
        # anything else, so I decided to just avoid the problem altogether.
        log += f"getting {self._name!r} parameter for {object.__repr__(obj)}"

        with self._checkout_bound_getters(obj, state, log) as bound_getters:
            values_iter = ValuesIter(
                    bound_getters,
                    self._get_default_cast(),
                    state.default,
                    log,
            )

            try:
                state.value = self._pick(values_iter)

            # Cache the exception indicating that this parameter is missing, 
            # since that is likely to be raised several times (and unlikely to 
            # terminate the program).
            #
            # Note that other exceptions will not update the cache, and 
            # therefore may need to be calculated on each access.  I could 
            # avoid this by catching all exceptions in this block, but that 
            # would make stack traces more confusing.  I think the approach of 
            # catching only `NoValueFound` strikes a good balance, but I'm open 
            # to revisiting this later.

            except NoValueFound as err:
                state.value = UNSPECIFIED
                state.exception = err
                state.meta = ExceptionMeta(err)

            else:
                state.exception = UNSPECIFIED
                state.meta = values_iter.meta
                state.dynamic = values_iter.dynamic

            state.cache_version = model_version

    @contextmanager
    def _checkout_bound_getters(self, obj, state=None, log=None):
        """
        Provide access to the bound getters, while guaranteeing that they will 
        be cleaned up when no longer needed.

        Bound getters are only meant to last for a single update.  However, its 
        possible that multiple callers will need access to the bound getters 
        over the course of a single lookup (particularly when shared keys are 
        involved).  This function ensures that the bound getters are available 
        to any caller that needs them, but that they are always properly 
        cleaned up.
        """
        state = state or self._load_state(obj)

        try:
            yield state.bound_getters

        except AttributeError:
            state.bound_getters = bg = self._calc_bound_getters(obj)

            try:
                yield bg

            finally:
                log = log or Log()

                for getter in state.bound_getters:
                    getter.cleanup(log)

                del state.bound_getters

    def _calc_bound_getters(self, obj):
        from ..configs.configs import Config
        from inspect import isclass

        keys = [
                Key(x) if isclass(x) and issubclass(x, Config) else x
                for x in self._keys or [self._get_default_key()]
        ]
        wrapped_configs = model.get_wrapped_configs(obj)
        are_getters = [isinstance(x, Getter) for x in keys]

        if all(are_getters):
            getters = keys

        elif any(are_getters):
            err = ApiError(
                    keys=keys,
            )
            err.brief = "can't mix string keys with Key/Method/Func/Value objects"
            err.info += lambda e: '\n'.join((
                    "keys:",
                    *map(repr, e['keys']),
            ))
            raise err

        elif len(keys) == 1:
            getters = [
                    ImplicitKey(wrapped_config, keys[0])
                    for wrapped_config in wrapped_configs
            ]

        elif len(keys) != len(wrapped_configs):
            err = ApiError(
                    configs=[x.config for x in wrapped_configs],
                    keys=keys,
            )
            err.brief = "number of keys must match number of configs"
            err.info += lambda e: '\n'.join((
                    f"configs ({len(e.configs)}):",
                    *map(repr, e.configs),
            ))
            err.blame += lambda e: '\n'.join((
                    f"keys ({len(e['keys'])}):",
                    *map(repr, e['keys']),
            ))
            raise err

        else:
            getters = [
                    ImplicitKey(wrapped_config, key)
                    for key, wrapped_config in zip(keys, wrapped_configs)
            ]

        return [getter.bind(obj, self) for getter in getters]

    def _prepare_cast_funcs(self, cast):
        return CastFuncs(cast)

    def _get_default_key(self):
        return self._name

    def _get_default_cast(self):
        return self._cast

    def _get_known_getter_kwargs(self):
        return set()



def _merge_default_args(instance, factory):
    have_instance = instance is not UNSPECIFIED
    have_factory = factory is not UNSPECIFIED

    if have_instance and have_factory:
        err = ApiError(
                instance=instance,
                factory=factory,
        )
        err.brief = "can't specify 'default' and 'default_factory'"
        err.info += "default: {instance}"
        err.info += "default_factory: {factory}"
        raise err

    if have_factory:
        return factory
    else:
        return lambda: instance

