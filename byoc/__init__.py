#!/usr/bin/env python3

"""
An object-oriented framework for command-line apps.
"""

__version__ = '0.29.0'

# Define the public API
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
from .getters import Key, Method, Func, Value
from .pickers import first
from .meta import meta_view
from .errors import NoValueFound
from .utils import lookup
