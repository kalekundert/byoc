#!/usr/bin/env python3

"""
An object-oriented framework for command-line apps.
"""

__version__ = '0.32.0'

# Define the public API
_pre_import_keys = set()
_pre_import_keys |= set(globals())

from .app import App, BareMeta
from .model import (
        init, load, reload, insert_config, insert_configs, append_config,
        append_configs, prepend_config, prepend_configs, share_configs,
        get_meta,
)
from .params.param import param
from .params.toggle import toggle_param, pick_toggled, Toggle as toggle
from .params.inherited import inherited_param
from .configs.configs import *
from .configs.layers import Layer, DictLayer, FileNotFoundLayer, dict_like
from .configs.attrs import config_attr
from .configs.on_load import on_load
from .getters import Key, Method, Attr, Func, Value
from .pick import first, list, merge_dicts
from .cast import Context, relpath, arithmetic_eval, float_eval, int_eval
from .key import jmes
from .meta import meta_view
from .errors import NoValueFound
from .utils import lookup

# Make everything imported above appear to come from this module:
_post_import_keys = set(globals())
for _key in _post_import_keys - _pre_import_keys:
    globals()[_key].__module__ = 'byoc'
del _pre_import_keys, _post_import_keys, _key

toggle.__name__ = 'toggle'
