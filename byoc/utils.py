#!/usr/bin/env python3

from .errors import *
from itertools import count
from collections.abc import Iterable

def noop(x):
    return x

def first_specified(*values, **kwargs):
    unspecified = kwargs.get('sentinel', None)

    for x in values:
        if x is not unspecified:
            return x

    try:
        return kwargs['default']
    except KeyError:
        err = ApiError(
                values=values,
                sentinel=unspecified,
        )
        err.brief = "must specify a value"
        err.blame += lambda e: f"given {len(e['values'])} {e.sentinel} values"
        err.hints += "did you mean to specify a default value?"
        raise err from None

def lookup(obj, key):
    """
    Lookup the given key in the given object.

    Arguments:
        obj: Any object.
        key:
            If callable: The callable will be called with the given object as 
            its only argument.  Whatever it returns will be taken as the value 
            of the key.

            If non-string iterable: The iterable will be considered as a 
            sequence of keys to iteratively lookup in the object.  In other 
            words, the return value will be something like 
            ``obj[key[0]][key[1]]...``.

            If anything else: The key will be looked up in the given object 
            like so: ``obj[key]``.
    """
    if callable(key):
        return key(obj)

    if isinstance(key, Iterable) and not isinstance(key, str):
        for subkey in key:
            obj = obj[subkey]
        return obj

    return obj[key]

class replay:
    """
    Provide a way to simultaneously iterate through the same iterator from 
    multiple different loops.

    Think of this class as an "iterator factory".  You can make new iterators 
    user the `iter()` built-in function:

        >>> def generator():
        ...     print("getting the first value")
        ...     yield 1
        ...     print("getting the second value")
        ...     yield 2
        ...
        >>> r = replay(generator())
        >>> r1 = iter(r)
        >>> r2 = iter(r)

    Each iterator made in this fashion will produce the same values in the same 
    order as the iterator provided to the constructor, regardless of the order 
    in which they are iterated through:

        >>> next(r1)
        getting the first value
        1
        >>> next(r2)
        1
        >>> next(r2)
        getting the second value
        2
        >>> next(r1)
        2
        >>> next(r1)
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        StopIteration
        >>> next(r2)
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        StopIteration
    """

    def __init__(self, iterator):
        self.iterator = iterator
        self.already_seen = []

    def __iter__(self):
        # We have to keep in mind that `self.already_seen` is shared between 
        # every invocation of this generator, so even if we run out of "already 
        # seen" values on one call, there might be more by the next.  So we 
        # need to do the `i >= len(...)` check every time.

        for i in count():
            original = False

            if i >= len(self.already_seen):
                try: value = next(self.iterator)
                except StopIteration: return
                self.already_seen.append(value)
                original = True

            yield self.already_seen[i], original


