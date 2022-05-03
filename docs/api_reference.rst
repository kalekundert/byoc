*************
API reference
*************

Apps
====
.. autosummary::
   :toctree: api

   byoc.App
   byoc.BareMeta
   byoc.init
   byoc.load
   byoc.reload
   byoc.on_load
   byoc.insert_config
   byoc.insert_configs
   byoc.append_config
   byoc.append_configs
   byoc.prepend_config
   byoc.prepend_configs
   byoc.share_configs

Configs
=======
.. autosummary::
   :toctree: api

   byoc.Config
   byoc.EnvironmentConfig
   byoc.CliConfig
   byoc.ArgparseConfig
   byoc.DocoptConfig
   byoc.AppDirsConfig
   byoc.FileConfig
   byoc.YamlConfig
   byoc.TomlConfig
   byoc.NtConfig
   byoc.JsonConfig
   byoc.Layer
   byoc.DictLayer
   byoc.FileNotFoundLayer
   byoc.config_attr
   byoc.dict_like
   byoc.lookup

Parameters
==========
.. autosummary::
   :toctree: api

   byoc.param
   byoc.inherited_param
   byoc.toggle_param
   byoc.toggle
   byoc.pick_toggled

Getters
=======
.. autosummary::
   :toctree: api

   byoc.Key
   byoc.Method
   byoc.Func
   byoc.Value

Key functions
=============
.. autosummary::
   :toctree: api

   byoc.jmes

Cast functions
==============
.. autosummary::
   :toctree: api

   byoc.relpath
   byoc.int_eval
   byoc.float_eval
   byoc.arithmetic_eval
   byoc.Context

Pick functions
==============
.. autosummary::
   :toctree: api

   byoc.first
   byoc.list
   byoc.merge_dicts

Metadata
========
.. autosummary::
   :toctree: api

   byoc.meta_view
   byoc.get_meta

Errors
======
.. autosummary::
   :toctree: api

   byoc.NoValueFound
