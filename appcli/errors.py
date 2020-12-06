#!/usr/bin/env python3

from tidyexc import Error

# These exceptions inherit from AtrtibuteError because appcli is only invoked 
# during attribute lookup, so all errors should inherit from AttributeError.

class AppcliError(Error, AttributeError):
    pass

# Rename to ApiError?
class ScriptError(AppcliError):
    # For errors configuring the App
    #
    # These errors are caused by the programmer.
    pass

# Rename to ParamError?  UsageError?
class ConfigError(AppcliError):
    # For errors returning parameters, e.g.
    # - cast function fails
    # - no value and no default
    #
    # These errors are caused by bad user input.
    pass

