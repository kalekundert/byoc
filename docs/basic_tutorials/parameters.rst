**********
Parameters
**********
Parameters are the means by which you specify which values are loaded from 
which configuration sources, and are probably the most important part of BYOC 
to understand.  They are created by defining `param` objects within the body of 
a class.  The snippet below shows the simplest possible example of this.  It 
creates a parameter named ``x``:

.. code-block::

    >>> import byoc
    >>> class MyApp:
    ...     x = byoc.param()

This parameter is not useful, though, since it doesn't know how to load values 
from any configuration sources.  To give a more realistic example, the 
following snippet shows a parameter that can load a value from a TOML file:

.. tab:: python

  .. code-block:: python

    >>> from byoc import TomlConfig
    >>> class MyApp:
    ...     __config__ = [TomlConfig.setup('conf.toml')]
    ...     x = byoc.param()
    ...
    >>> app = MyApp()
    >>> app.x
    1

.. tab:: conf.toml

  .. code-block:: toml

    x = 1

Don't pay too much attention to the `TomlConfig` lines yet.  They'll be the 
focus of the :doc:`configs` tutorial.  Suffice to say that they tell the app 
about a TOML file called ``conf.toml`` from which parameters can be read.

As in the first snippet, the `param` is instantiated without any arguments.  
The many arguments that `param` can take will be described below, but the 
no-argument default is to look in each known config for a value with the same 
name as the parameter itself, which in this case is ``x``.  The TOML file has 
such a value, and so when we access this parameter we get the value from the 
TOML file.

Note that parameters can be assigned any value you'd like from within python, 
just like normal attributes.  Values assigned like this will always take 
precedence over values read from various config sources (which are best thought 
of as default values).  That said, you can always go back to the config value 
by deleting the attribute:

.. code-block::

  >>> app.x = 2
  >>> app.x
  2
  >>> del app.x
  >>> app.x
  1

Finding values
==============
Each parameter must specify all the places where a value could be provided, 
e.g. the command-line, one or more config files, a method call within python, 
etc.  This is done by passing any number of "getter" objects to the parameter 
constructor.  Each getter specifies one place where a value can be found.  The 
order in which the getters are passed determines the order in which those 
places will be searched.  There are 4 kinds of getters:

- `Key`
- `Method`
- `Func`
- `Value`

Key
---
`Key` specifies how to load a value from a `Config`.  It is by far the most 
commonly-used getter.  The following snippet shows a parameter ``x`` that uses 
`Key` to read a value ``y`` from a config file:

.. tab:: python

  .. code-block:: python

    >>> from byoc import Key
    >>> class MyApp:
    ...     __config__ = [TomlConfig.setup('conf.toml')]
    ...     x = byoc.param(
    ...             Key(TomlConfig, 'y'),
    ...     )
    ...
    >>> app = MyApp()
    >>> app.x
    1

.. tab:: conf.toml

  .. code-block:: toml

    y = 1

`Key` takes two arguments.  The first specifies which configs to search, and 
the second specifies which values to retrieve from those configs.  More 
specifically, the first argument should be a `Config` class.  All configs of 
that class (or its subclasses) associated with the app in question will be 
searched for values.  Note that it's sometimes useful to choose a class that 
will match several configs (e.g. `FileConfig` will match both `TomlConfig` and 
`YamlConfig`).  It's also sometimes necessary to subclass existing configs just 
to make them distinguishable (e.g. if you want to read from two TOML files with 
different semantics).  Most commonly, though, this argument is simply a class 
that exactly matches one of the configs (as in the example above).

The second argument specifies which value to retrieve from the config.  This 
argument can take three forms:

- Hashable (e.g. string, integer, etc.): These values are taken as keys and 
  used to index into the data structure loaded by the config.  Most configs 
  load dictionaries, so it makes sense to think of this argument as a 
  dictionary key, but be aware that configs are allowed to load whatever data 
  structures they want.

- Iterable: These values are taken as a series of keys to apply iteratively to 
  the data structure loaded by the config.  For example, ``['a', 'b']`` would 
  return ``1`` for a TOML file with the following key: ``a.b = 1``.  Each item 
  in the iterable is treated as a non-iterable, non-callable key.  So it's not 
  possible to nest iterables, or to include callables in the iterable.  Note 
  also that strings are not counted as iterables.

- Callable: The callable will be invoked with the data structure loaded by the 
  config as it's only argument.  Whatever value it returns will be passed on to 
  the parameter.  This is the most flexible form of this argument, and should 
  be used when neither of the simpler forms suffice.  Note that the callable 
  should not modify the data structure passed to it.

If no key is specified, the name of the parameter will be used as the default.  
If a `KeyError` is raised when attempting to lookup a key, the key will be 
silently ignored and the parameter will continue searching for a value.

One common reason to use the callable form of the second argument is to combine 
multiple values into one.  For example, the following snippet merges ``x`` and 
``y`` fields from a config file into a ``coord`` parameter:

.. tab:: python

  .. code-block:: python

    >>> class MyApp:
    ...     __config__ = [TomlConfig.setup('conf.toml')]
    ...     coord = byoc.param(
    ...             Key(TomlConfig, lambda d: (d['x'], d['y'])),
    ...     )
    ...
    >>> app = MyApp()
    >>> app.coord
    (1, 2)

.. tab:: conf.toml

  .. code-block:: toml

    x = 1
    y = 2

One callable worth briefly highlighting is `jmes`.  It applies a JMESPath_ 
query to the dictionary provided by the config, which is very useful for 
extracting information from highly nested data structures.  As a simple 
example, we can reimplement the above example:

.. tab:: python

  .. code-block:: python

    >>> from byoc import jmes
    >>> class MyApp:
    ...     __config__ = [TomlConfig.setup('conf.toml')]
    ...     coord = byoc.param(
    ...             Key(TomlConfig, jmes('[x,y]')),
    ...     )
    ...
    >>> app = MyApp()
    >>> app.coord
    [1, 2]

.. tab:: conf.toml

  .. code-block:: toml

    x = 1
    y = 2

This has been a long subsection, but it's very important to be comfortable 
using `Key` to specify where exactly a parameter should get its value from.  
We've now pretty much said everything there is to say on this topic, but I'll 
leave you with one last example showing a more realistic use case than any of 
the previous examples.  This script prints a value specified either via the 
command-line or via a config file, with the command-line taking precedence:

.. tab:: my_app.py

  .. code-block:: python

    import byoc
    from byoc import Key, DocoptConfig, TomlConfig

    class MyApp:
        """\
        Usage:
            my_app.py [<x>]
        """
        __config__ = [
                DocoptConfig,
                TomlConfig.setup('conf.toml'),
        ]
        x = byoc.param(
                Key(DocoptConfig, '<x>'),
                Key(TomlConfig, 'x'),
        )
    
    app = MyApp()
    byoc.load(app, DocoptConfig)
    print(app.x)

.. tab:: conf.toml

  .. code-block:: toml

    x = 1

.. tab:: bash

  .. code-block:: bash

    $ python my_app.py
    1
    $ python my_app.py 2
    2

This script introduces `DocoptConfig` in addition to `TomlConfig`.  Briefly, 
`DocoptConfig` parses command-line arguments in the manner specified by the 
class docstring.  Don't worry about these lines too much, though.  The 
important point is that there are two configs, and the ``x`` parameter can make 
use of both.

Note that the command-line takes precedence because the `DocoptConfig` key was 
specified before the `TomlConfig` one.  Also note that the two configs use 
different keys.

.. _JMESPath: https://jmespath.org/

Implicit keys
-------------
Explicitly constructing `Key` getters is somewhat verbose, and it's sometimes 
convenient to use a more succinct syntax.  As we learned in the previous 
section, constructing a `Key` requires two pieces of information: a config 
class and a hashable/iterable/callable key to look up in any matching 
corresponding configs.  The more succinct syntax is to pass one of these pieces 
of information directly to `param`, and to infer the other from context.  Be 
careful when using this syntax, though, because it's much more fragile than the 
explicit syntax.  I personally avoid implicit keys for all but the simplest 
programs.

The first way to implicitly specify keys is using config classes.  In this 
case, the lookup key is taken to be the parameter name.  To demonstrate this, 
we'll make an app with two TOML configs referring to two different files.  
We'll then use just the config class to specify which parameter reads from 
while file:

.. tab:: python

  .. code-block:: python

    >>> class TomlConfig1(TomlConfig):
    ...     path_getter = lambda app: 'conf_1.toml'
    ...
    >>> class TomlConfig2(TomlConfig):
    ...     path_getter = lambda app: 'conf_2.toml'
    ...
    >>> class MyApp:
    ...     __config__ = [
    ...             TomlConfig1,
    ...             TomlConfig2,
    ...     ]
    ...     x = byoc.param(TomlConfig1)
    ...     y = byoc.param(TomlConfig2)
    ...
    >>> app = MyApp()
    >>> app.x
    1
    >>> app.y
    2

.. tab:: conf_1.toml

  .. code-block:: toml

    x = 1
    y = 1

.. tab:: conf_2.toml

  .. code-block:: toml

    x = 2
    y = 2

The second way to implicitly specify keys is using lookup keys (i.e. the second 
argument to `Key`, which can be hashable/iterable/callable).  If only one such 
key is specified, it will be used for every config available to the app.  
Otherwise, the number of keys must match the number of configs and they will be 
paired based on the order of the ``__config__`` variable.  I personally only 
use this syntax with simple apps that will only ever have one config (usually 
`DocoptConfig`), as in the following example:

.. tab:: my_app.py

  .. code-block:: python
   
    import byoc
    from byoc import DocoptConfig

    class MyApp:
        """
        Usage:
            my_app <x>
        """
        __config__ = [DocoptConfig]
        x = byoc.param('<x>')
    
    app = MyApp()
    byoc.load(app, DocoptConfig)
    print(app.x)

.. tab:: bash

  .. code-block:: bash

    $ python my_app.py 1
    1
    $ python my_app.py 2
    2

The third and final way to implicitly specify keys is to leave the argument 
list blank.  In this case, the name of the parameter will be applied to every 
config available to the app:

.. tab:: python

  .. code-block:: python

    >>> class MyApp:
    ...     __config__ = [
    ...             TomlConfig.setup('conf.toml'),
    ...     ]
    ...     x = byoc.param()
    ...
    >>> app = MyApp()
    >>> app.x
    1

.. tab:: conf.toml

  .. code-block:: toml

    x = 1

Note that you cannot mix implicit and explicit keys.  So if one key needs to be 
explicit for any reason, they all need to be explicit.  Likewise, if you want 
to mix `Key` getters with `Method`/`Func`/`Value` getters, you also need to use 
explicit keys.

Method, Func, and Value
-----------------------
In contrast to the `Key` getter, the `Method`, `Func`, and `Value` getters get 
values directly from python.  The differences between these three are pretty 
straight-forward:

- `Method` gets a value by calling a method, i.e. a function that takes an app 
  instance as its only argument.
- `Func` gets a value by calling a no-argument function.
- `Value` returns a hard-coded value.

The following example shows how all of these getters can be used:

.. code-block:: python

  >>> from byoc import Value, Func, Method
  >>> class MyApp:
  ...
  ...     def __init__(self, arg):
  ...         self.arg = arg
  ...
  ...     def get_arg(self):
  ...         return self.arg
  ...
  ...     v = byoc.param(Value(0))
  ...     f = byoc.param(Func(dict))
  ...     m = byoc.param(Method(get_arg))
  ...
  >>> app1, app2 = MyApp(1), MyApp(2)
  >>> app1.v, app2.v
  (0, 0)
  >>> app1.f, app2.f
  ({}, {})
  >>> app1.f is not app2.f
  True
  >>> app1.m, app2.m
  (1, 2)

The following example shows a more real example of how `Method` might be used.  
It also shows how `Method` can be used to make one parameter depend on the 
value of another, a very useful ability.  The idea behind this example is to 
make an app that reads an input file and writes an output file.  The name of 
the output file can be explicitly given, or it can be inferred from the name of 
the input file:

.. tab:: my_app.py

  .. code-block:: python
   
    import byoc
    from byoc import Key, Method, DocoptConfig
    from pathlib import Path

    class MyApp:
        """
        Usage:
            my_app <in> [<out>]
        """
        __config__ = [DocoptConfig]

        in_path = byoc.param(
                Key(DocoptConfig, '<in>'),
                cast=Path,
        )
        out_path = byoc.param(
                Key(DocoptConfig, '<out>'),
                Method(lambda self: self.in_path.with_suffix('.out')),
                cast=Path,
        )
    
    app = MyApp()
    byoc.load(app, DocoptConfig)
    print(app.out_path)

.. tab:: bash

  .. code-block:: bash

    $ python my_app.py data.in
    data.out
    $ python my_app.py input output
    output

This example makes use of the *cast* argument, which hasn't been mentioned yet 
but will be introduced in the `Parsing values`_ section.  Hopefully it's role 
here is pretty clear, though: it converts the strings read from the 
command-line into `pathlib.Path` instances.

`Method` and `Func` both accept a *skip* argument, which specifies how 
exceptions should be handled.  The *skip* argument should be a tuple of 
exception types.  If any of these exceptions are raised by the method/function 
in question, they will be silently ignored and the parameter will continue 
searching for a value.  Any other exceptions will be allowed to propagate.

By default, `Func` does not skip any exceptions and `Method` skips only 
`NoValueFound` exceptions.  `NoValueFound` is a BYOC-specific exception that is 
raised (by default) when a parameter fails to find a value.  What this means is 
that methods which depend on other BYOC parameters will fail gracefully when 
those parameters don't have values.

Defaults
--------
Parameters can also specify default values, to be used when none of the getters 
find an appropriate value.  There are two ways to specify a default: the 
*default* argument and the *default_factory* argument.  The former simply 
specifies a value to use as the default.  The latter specifies a function that 
will be called exactly once per instance to create the default value.  The 
purpose of this is to allow mutable objects, like list and dictionaries, to be 
defaults without their values being shared between app instances.

You can specify either *default* or *default_factory*, but not both.  If you 
specify neither, it is assumed (by default) that a `NoValueFound` exception 
should be raised if not value can be found for the parameter in question.  The 
following example shows how to use these arguments:

.. code-block::

  >>> class MyApp:
  ...     x = byoc.param(default=1)
  ...     y = byoc.param(default_factory=list)
  ...     z = byoc.param()  # no default
  ...
  >>> app = MyApp()
  >>> app.x
  1
  >>> app.y
  []
  >>> app.z
  Traceback (most recent call last):
      ...
  byoc.NoValueFound: can't find value for parameter
  • getting 'z' parameter for <MyApp object at 0x7f225d336700>
  • nowhere to look for values
  • did you mean to provide a default?

Note that different app instances have different ``y`` lists:

.. code-block::

  >>> app1, app2 = MyApp(), MyApp()
  >>> app1.y.append(1)
  >>> app2.y.append(2)
  >>> app1.y, app2.y
  ([1], [2])

You may have noticed that these *default* arguments behave very much like the 
`Value` and `Func` getters.  This is true, but there are a few small 
differences that make the *default* arguments better suited for the task of 
specifying default values:

- The *cast* function (described in the `Parsing values`_ section) is not 
  applied to the default value.

- The *default_factory* function is only called once per instance, while the 
  `Func` function may be called more often depending on the cache settings of 
  the parameter (although by default it will also only be called once per 
  instance).

- The *default* arguments are a bit more succinct and semantic.


Parsing values
==============
If often necessary to do some processing on user-provided input values.  To 
give some common examples, you might want to:

- Convert a string to an int/float.
- Convert a comma-separated string to a list.
- Convert a relative path to an absolute path.
- Evaluate an arithmetic expression.
- Invert the meaning of a boolean flag.
- And so on...

*Cast* argument
---------------
The first way to do this kind of processing is to specify the *cast* argument 
to `param`.  This argument accepts either a callable or a list of callables.  
Each callable should accept a single argument (the value to process) and return 
a single value (the processed value).  If multiple callables are given, each 
will be called in order.  Here is a simple example showing how to evaluate an 
arithmetic expression read from a config file:

.. tab:: python

  .. code-block:: python

    >>> class MyApp:
    ...     __config__ = [
    ...             TomlConfig.setup('conf.toml'),
    ...     ]
    ...     x = byoc.param(
    ...             cast=byoc.int_eval,
    ...     )
    ...
    >>> app = MyApp()
    >>> app.x
    3

.. tab:: conf.toml

  .. code-block:: toml

    x = "1 + 2"

Getters (e.g. `Key`) also accept a *cast* argument.  It works in the same way, 
except that it only applies to values loaded by that getter.  It's not uncommon 
to simultaneously specify *cast* for `param` and one or more getters.  In this 
case, the functions specified by the getter are applied before those specified 
by the parameter.  This is useful when different configuration sources require 
some unique and some shared processing steps.  For example, the following 
script loads a set from either a config file or the command line.  The value 
from the config file is expected to be a list (which can be directly converted 
to a set), while the value from the command line is expected to be a 
comma-separated string (which needs to be split into a list before being 
converted to a set):

.. tab:: my_app.py

  .. code-block:: python

    import byoc
    from byoc import Key, DocoptConfig, TomlConfig

    def comma_list(value):
        return value.split(',')

    class MyApp:
        """\
        Usage:
            my_app.py [<x>]
        """
        __config__ = [
                DocoptConfig,
                TomlConfig.setup('conf.toml'),
        ]
        x = byoc.param(
                Key(DocoptConfig, '<x>', cast=comma_list),
                Key(TomlConfig, 'x'),
                cast=set,
        )
    
    app = MyApp()
    byoc.load(app, DocoptConfig)
    print(app.x)

.. tab:: conf.toml

  .. code-block:: toml

    x = ['a', 'b']

.. tab:: bash

  .. code-block:: bash

    $ python my_app.py
    {'a', 'b'}
    $ python my_app.py b,c
    {'b', 'c'}

Although it's beyond the scope of this tutorial, it's worth mentioning that 
*cast* functions can gain access to the object that owns the parameter (i.e.  
*self*) and to metadata describing how the value in question was loaded.  The 
built-in `relpath` cast function uses this metadata to interpret paths relative 
to whichever file they were specified in.  For more information, refer to the 
`Context` class.

*Get* argument
--------------
Another way to process inputs is using the *get* argument to `param`.  This 
argument specifies a function that will be invoked every time the parameter is 
accessed.  In contrast, *cast* functions are invoked only when a new value is 
loaded.  It may be helpful to think of the *get* argument as allowing a `param` 
to behave something like a `property`.  The given function will be called with 
two arguments: *self* and the value to process.

It's best to only use *get* if you really need to, because it's called much 
more often than *cast* and precludes the most aggressive form of caching.  But 
it's useful in scenarios where you have parameters whose values depend on other 
attributes of the app.  For example, consider a program that has two modes 
(e.g. "fast" and "slow") and two scalar configuration parameters (e.g. "x" and 
"y").  We want users to be able to specify values for these parameters in two 
ways: either directly as scalars, or as dictionaries with different values for 
each mode.  Here's how we can use the *get* argument to do this:

.. tab:: my_app.py

  .. code-block:: python

    import byoc
    from byoc import Key, ArgparseConfig, TomlConfig
    from argparse import ArgumentParser

    def lookup_mode(app, value):
        if isinstance(value, dict):
            return value[app.mode]
        else:
            return value

    class MyApp:
        __config__ = [
                ArgparseConfig,
                TomlConfig.setup('conf.toml'),
        ]
        mode = byoc.param(ArgparseConfig)
        x = byoc.param(TomlConfig, get=lookup_mode)
        y = byoc.param(TomlConfig, get=lookup_mode)

        def get_argparse(self):
            p = ArgumentParser()
            p.add_argument('mode')
            return p
    
    app = MyApp()
    byoc.load(app, ArgparseConfig)
    print(app.x, app.y)

.. tab:: conf.toml

  .. code-block:: toml

    x = 1
    y.fast = 2
    y.slow = 3

.. tab:: bash

  .. code-block:: bash

    $ python my_app.py fast
    1 2
    $ python my_app.py slow
    1 3

*Schema* argument
-----------------
Finally, many configs (not parameters) accept a *schema* argument that can be 
used to apply a function to all of the values loaded from that config source.  
This argument is unique in that it can inspect config values before they are 
accessed.  One important use case for this is to make sure than no unexpected 
config values were specified.  Such values would otherwise be silently ignored, 
since they wouldn't be referenced by any parameters, possibly leading to subtle 
bugs (e.g. a default value being used instead of a misspelled config value).

The :doc:`configs` tutorial will more thoroughly describe how configs work and 
what arguments (like *schema*) they accept, but it's worth briefly describing 
how to use a schema here.  The schema argument should be a callable that 
accepts the values loaded by the config in question (usually a dictionary but 
could be anything) and either returns a processed form of those values or 
raises an exception if any problems are found.  You can of course write your 
own schema functions, but it's more common to use a third-party library like 
voluptuous_, schema_, pydantic_, cerberus_, valideer_, jsonschema_, etc.

This example shows the situation mentioned above, where (i) our app has a 
parameter *x* that may optionally be defined in a config file and (ii) we 
accidentally misspelled that parameter "X" (i.e. uppercase instead of 
lowercase) in said file.  Instead of silently falling back on the default 
value, the schema detects the unexpected value and raises an exception as soon 
as the app is loaded:

.. tab:: python

  .. code-block:: python

    >>> from voluptuous import Schema, Optional
    >>> class MyApp:
    ...     __config__ = [
    ...             TomlConfig.setup(
    ...                 'conf.toml',
    ...                 schema=Schema({Optional('x'): int}),
    ...             ),
    ...     ]
    ...     x = byoc.param(default=0)
    ...
    >>> app = MyApp()
    >>> app.x
    Traceback (most recent call last):
       ...
    voluptuous.error.MultipleInvalid: extra keys not allowed @ data['X']

.. tab:: conf.toml

  .. code-block:: toml

    X = 1

.. _voluptuous: https://github.com/alecthomas/voluptuous
.. _schema: https://github.com/keleshev/schema
.. _pydantic: https://pydantic-docs.helpmanual.io/
.. _cerberus: https://docs.python-cerberus.org/en/stable/
.. _valideer: https://github.com/podio/valideer
.. _jsonschema: https://python-jsonschema.readthedocs.io/en/latest/


Picking values
==============
So far, all of the parameters we've considered have had simply adopted the 
first value they've been able to find.  Sometimes, though, you might instead 
want to integrate values from multiple configuration sources.  For example, 
this comes up if you want to make use of "profiles" defined in both system-wide 
and user-specific configuration files.

The *pick* argument to `param` provides the means to do things like this.  This 
argument takes a function that will be called with a single argument—an 
iterable that will generate (on demand) every value that can be found for the 
parameter in question—and returns a value for the parameter to adopt.  BYOC 
provides several built-in pick functions, namely `first`, `list`, and 
`merge_dicts`.  The following example shows how to use `merge_dicts`:

.. tab:: python

  .. code-block:: python

    >>> class MyApp:
    ...     __config__ = [
    ...             TomlConfig.setup('conf_1.toml'),
    ...             TomlConfig.setup('conf_2.toml'),
    ...     ]
    ...     x = byoc.param(pick=byoc.merge_dicts)
    ...
    >>> app = MyApp()
    >>> app.x
    {'a': 1, 'b': 2}

.. tab:: conf_1.toml

  .. code-block:: toml

    x.a = 1

.. tab:: conf_2.toml

  .. code-block:: toml

    x.b = 2

It's a bit outside the scope of this tutorial, but another (optional) 
responsibility of the pick function is to keep track of the metadata associated 
with the values it processes.  This metadata describes where each value was 
loaded from and is meant to help generate useful error messages (e.g. "this 
value that caused a problem was loaded from this specific line in this specific 
file").  The iterable passed to the pick function has a ``with_meta`` property 
that iterates over ``value, meta`` tuples (as opposed to the iterable itself, 
which just iterates over the values).  Typically, the pick function will 
organize the metadata in a data structure that parallels the values themselves 
(e.g. a list for `list`, a dictionary for `merge_dicts`).  This metadata 
structure is finally assigned to the ``meta`` attribute of the iterable, where 
BYOC will find it a associate it with the parameter.  All of the builtin pick 
function preserve metadata in this fashion.  If you're writing your own pick 
function, though, there's no need to worry about this unless you have plans to 
use the metadata for something.


