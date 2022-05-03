********
Overview
********

Before reading the rest of the tutorials, it's worth taking a moment to 
familiarize yourself with the big-picture components of BYOC and the ways they 
work together:

App
  An app is any class that uses BYOC.  There is an `App` class, but apps don't 
  actually need to inherit from it.  It just provides some conveniences, like a 
  main function that can be invoked as an entry point and the ability to 
  instantiate objects with no arguments (i.e. purely from BYOC parameters) even 
  if the constructor has arguments.
  
Config
  A `Config` is an object that describes a single source of configuration 
  information.  For example, `DocoptConfig` reads information from the 
  command-line, `TomlConfig` reads information from one or more TOML files, 
  `EnvironmentConfig` reads information from environment variables, etc.  BYOC 
  has a number of useful built-in configs, but it's also easy (and not 
  uncommon) to write your own.

Parameter
  A parameter is a `descriptor` that knows how to query each relevant 
  configuration source for a particular value.  For example, a parameter for a 
  file path might take the following steps to get a value:

  - Look for a command line argument named ``--path``.
  - Look in a configuration file for a key named ``path``.
  - Use the first value found.
  - Convert that value to a `pathlib.Path`.

  More generally, parameters control (i) the order in which configuration 
  sources are searched, (ii) which keys are used with which sources, (iii) how 
  to parse/validate values, (iv) which values to keep/discard/merge, (v) what 
  to do if no values are found, (vi) whether or not to use caching, etc.

Getter
  A getter is an argument to a parameter that knows how to look up one value 
  from one configuration source.  In the file path example above, there 
  would've been two getters: one for the command line and one for the 
  configuration file.  Parameters can take any number of getter arguments, and 
  the order of those arguments determines the order in which configuration 
  sources are considered.

  The most common getter is `Key`, which knows how to lookup a value from 
  specific types of `Config` objects associated with the app.  The other 
  getters are `Method`, `Func`, and `Value`.  These three don't lookup values 
  from external sources, but instead make it easy to "look up" values 
  calculated in python.

