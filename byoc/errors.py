#!/usr/bin/env python3

import textwrap
from tidyexc import Error

class ApiError(Error):
    """
    For errors using the API, e.g. calling function with inconsistent/redundant 
    arguments.

    These errors are always caused by the programmer, and can never be 
    triggered by end-user input.
    """
    pass

class NoValueFound(AttributeError):
    """
    The default exception raised when no value can be found for a parameter.

    BYOC tries to avoid raising or interpreting any exceptions relating to 
    accessing parameter values.  Instead, user-provided callbacks are expected 
    to raise if they notice something wrong.  This puts the user in control of 
    exception handling and error messages, both good things for a 
    general-purpose framework like this.

    `NoValueFound` is a bit of an exception to this philosophy.  It's raised by 
    the default picker (`first`) in the event that no values were found for an 
    parameter.  It's interpreted by some parts of BYOC (specifically the 
    `Method` and `Func` getters) to mean that an attempt to get a value should 
    be silently skipped.  Both of these behaviors can be overridden, but 
    they're useful defaults.
    """

    def __init__(self, message, log):
        super().__init__(message + '\n' + log.format())

class Log:
    """
    A record of the search for a parameter value.

    Messages are added to the log using the ``+=`` operator::

        >>> log = Log()
        >>> log += "hello world!"

    Each message can either be a string or a no-argument callable returning a 
    string.  The callables will be evaluated just before the log is displayed, 
    and can be used to defer the construction of strings that are likely to be 
    expensive and/or unlikely to be useful.  For example, it's common to use 
    callables to log when a value is successfully found, because (i) the log is 
    usually only displayed in cases where no value is found and (ii) formatting 
    arbitrary objects could be expensive.
    """
    
    def __init__(self):
        self._messages = []

    def __str__(self):
        return self.format()

    def __iadd__(self, message):
        """
        Add the given message to the log.
        """
        self._messages.append(message)
        return self

    def info(self, message):
        """
        Add the given message to the log.

        The ``+=`` operator is the preferred way to do this.  Only use this 
        method if the ``+=`` operator is inconvenient for some reason (e.g. its 
        not allowed in lambda functions).
        """
        self += message

    @property
    def message_strs(self):
        return [
                m() if callable(m) else m
                for m in self._messages
        ]

    def format(self):
        out = ''
        bullet = '• '
        indent = ' ' * len(bullet)

        for msg in self.message_strs:
            msg = textwrap.indent(msg, indent)
            msg = bullet + msg[len(bullet):]
            out += msg + '\n'

        return out[:-1]

