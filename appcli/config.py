#!/usr/bin/env python3

import inspect
import functools
from pathlib import Path
from more_itertools import one, first
from .utils import lookup, first_specified
from .errors import ConfigError

# Brainstorming
# =============
# Requirements:
# - Defined order
# - Have name
# - Have arguments (e.g. path for file)

# Have config return dictionary:
# - Can standardize tricks for handling nested keys.
# - Wrap in Param instance to simultaneously return "location".
#
# Have config present getter API:
# - Easier to implement configs where it may not make sense to load everything 
#   at once, e.g. remote resources, massive configs, etc.
# - That said, such configs could always return something that implements the 
#   dict interface and does whatever it wants.
# - Seems more complicated, for little benefit.

# There are groups of configs:
# - Groups that share the same keys
# - Groups that should be loaded always vs. conditionally (e.g. on main())
# - Groups that share cast functions.
#
#
# In the use cases I have in mind, these groups will match, but that won't 
# necessarily be the case.  
#
# I should have the ability to set the groups at config time, but for the most 
# part I should be able to pick defaults that work.

class Config:
    tag = None
    key_group = None
    cast_group = None
    require_explicit_load = False

    def __init__(self, *, tag=None, key_group=None, cast_group=None, autoload=None):
        self.init(
                tag=tag,
                key_group=key_group,
                cast_group=cast_group,
                autoload=autoload,
        )

    def init(self, *, tag=None, key_group=None, cast_group=None, autoload=None): 
        self.key_group = first_specified(
                key_group,
                self.key_group,
                tag,
                self.tag,
                default=None,
        )
        self.cast_group = first_specified(
                cast_group,
                self.cast_group,
                tag,
                self.tag,
                default=None,
        )
        self.require_explicit_load = (
                not autoload
                if autoload is not None else
                self.require_explicit_load
        )
        return self

    def load(self, obj):
        # Return list of Layer instances
        #
        # By returning a list, makes it easy to nest configs
        raise NotImplmentedError


class DictConfig(Config):
    tag = 'dict'

    def __init__(self, **kwargs):
        self.dict = kwargs
        frame = inspect.stack()[1]
        self.location = f'{frame.filename}:{frame.lineno}'

    def load(self, obj):
        return Layer(
                values=self.dict,
                location=self.location,
        )

class AttrConfig(Config):
    """
    Read parameters from another attribute of the object.
    """
    tag = 'attr'

    def __init__(self, attr, **kwargs):
        super().__init__(**kwargs)
        self.attr = attr

    def load(self, obj):

        @not_found(AttributeError)
        def getter(key):
            x = getattr(obj, self.attr)
            return lookup(x, key)

        cls = obj.__class__
        return Layer(
                values=getter,
                location=f'{inspect.getmodule(cls).__name__}.{cls.__qualname__}.{self.attr}',
        )


class ArgparseConfig(Config):
    tag = 'argparse'
    require_explicit_load = True

    def __init__(self, parser_getter='get_argparse', **kwargs):
        super().__init__(**kwargs)
        self.parser_getter = parser_getter
        self.parser = None

    def load(self, obj):
        import docopt

        parser = self.get_parser(obj)
        args = parser.parse_args()

        return Layer(
                values=vars(args),
                location='command line',
        )

    def get_parser(self, obj):
        if not self.parser:
            self.parser = getattr(obj, self.parser_getter)()
        return self.parser

    def get_usage(self, obj):
        return self.get_parser(obj).format_help()

    def get_brief(self, obj):
        return self.get_parser(obj).description


class DocoptConfig(Config):
    tag = 'docopt'
    require_explicit_load = True

    def __init__(self, doc_attr='__doc__', **kwargs):
        super().__init__(**kwargs)
        self.doc_attr = doc_attr

    def load(self, obj):
        import docopt

        args = docopt.docopt(self.get_usage(obj))
        args = {k: v for k, v in args.items() if v is not None}

        return Layer(
                values=args,
                location='command line',
        )

    def get_usage(self, obj):
        return getattr(obj, self.doc_attr).format(obj)

    def get_brief(self, obj):
        import re
        sections = re.split('usage:', self.get_usage(obj), flags=re.IGNORECASE)
        return first(sections, '').strip()


class AppDirsConfig(Config):
    tag = 'file'

    def __init__(self, name=None, format=None, slug=None, author=None, version=None, schema=None,
            stem='conf', **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.stem = stem
        self.slug = slug
        self.author = author
        self.version = version
        self.config_cls = format
        self.schema = schema

    def load(self, obj):
        dirs = self.get_dirs(obj)
        name, config_cls = self.get_name_and_config_cls()
        paths = [
                Path(dirs.user_config_dir) / name,
                Path(dirs.site_config_dir) / name,
        ]
        return [
                config_cls(p, schema=self.schema).load(obj)
                for p in paths
        ]

    def get_name_and_config_cls(self):
        if not self.name and not self.config_cls:
            raise ConfigError("must specify `AppDirsConfig.name` or `AppDirsConfig.format`")

        if self.name and self.config_cls:
            err = ConfigError(
                    name=self.name,
                    format=self.config_cls,
            )
            err.brief = "can't specify `AppDirsConfig.name` and `AppDirsConfig.format`"
            err.info += "name: {name!r}"
            err.info += "format: {format!r}"
            err.hints += "use `AppDirsConfig.stem` to change the filename used by `AppDirsConfig.format`"
            raise err

        if self.name:
            suffix = Path(self.name).suffix
            configs = [
                    x for x in FileConfig.__subclasses__()
                    if suffix in getattr(x, 'suffixes', ())
            ]
            found_these = lambda e: '\n'.join([
                    "found these subclasses:", *(
                        f"{x}: {' '.join(getattr(x, 'suffixes', []))}"
                        for x in e.configs
                    )
            ])
            with ConfigError.add_info(
                    found_these,
                    name=self.name,
                    configs=FileConfig.__subclasses__(),
            ):
                config = one(
                        configs,
                        ConfigError("can't find FileConfig subclass to load '{name}'"),
                        ConfigError("found multiple FileConfig subclass to load '{name}'"),
                )

            return self.name, config

        if self.config_cls:
            return self.stem + self.config_cls.suffixes[0], self.config_cls

    def get_dirs(self, obj):
        from appdirs import AppDirs
        slug = self.slug or obj.__class__.__name__.lower()
        return AppDirs(slug, self.author, version=self.version)
        

class FileConfig(Config):
    tag = 'file'

    def __init__(self, path, schema=None, **kwargs):
        super().__init__(**kwargs)
        self.path = Path(path)
        self.schema = schema

    def load(self, obj):
        data = self._do_load()

        if callable(self.schema):
            data = self.schema(data)

        return Layer(
                values=data,
                location=self.path,
        )

    def _do_load(self, app):
        pass

class YamlConfig(FileConfig):
    suffixes = '.yml', '.yaml'

    def _do_load(self):
        import yaml
        with open(self.path) as f:
            return yaml.safe_load(f)


class TomlConfig(FileConfig):
    suffixes = '.toml',

    def _do_load(self):
        import toml
        return toml.load(self.path)

class NtConfig(FileConfig):
    suffixes = '.nt',

    def _do_load(self):
        import nestedtext as nt
        return nt.load(self.path)



class Layer:

    def __init__(self, *, values, location):
        # Values: any object that:
        # - implements __getitem__ to either return value associated with Key, 
        #   or raise KeyError
        # - is a callable that takes a key as the only argument, and raises 
        #   KeyError if not found
        self.config = None
        self.values = values
        self.location = location

    def __repr__(self):
        return f'Layer(values={self.values!r}, location={self.location!r})'

class PendingLayer:

    def __init__(self, config):
        self.config = config

    def __repr__(self):
        return f'PendingLayer(config={self.config!r})'

def not_found(*raises):
    """
    Wrap the given function so that a KeyError is raised if any of the expected 
    kinds of exceptions are caught.

    This is meant to help implement the interface expected by `Layers.values`, 
    i.e. a callable that raises a KeyError if a value could not successfully be 
    found.
    """

    def decorator(f):

        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except raises as err:
                raise KeyError from err

        return wrapped
        
    return decorator

