#!/usr/bin/env python3

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
    `Method` and `Function` getters) to mean that an attempt to get a value 
    should be silently skipped.  Both of these behaviors can be overridden, but 
    they're useful defaults.
    """

    def __init__(self, *args):
        super().__init__('\n'.join(str(x).strip() for x in args))

class Log:
    
    def __init__(self):
        # This is a bit of a hack.  We're just using the error class for its 
        # formatting features.
        #
        # If I ever get around to refactoring this, note that the unit tests 
        # rely on being able to access list of all log messages with parameters 
        # substituted but without bullet points applied.
        self._err = Error()

    def __str__(self):
        return str(self._err)

    def info(self, message, **kwargs):
        self._err.put_info(message, **kwargs)

    def hint(self, message):
        self._err.info += message
