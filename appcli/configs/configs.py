#!/usr/bin/env python3

import sys, os, re, inspect
from pathlib import Path
from textwrap import dedent
from more_itertools import one, first
from .layers import Layer, dict_like
from ..utils import lookup, first_specified
from ..errors import ConfigError

class Config:
    autoload = True

    def load(self, obj):
        raise NotImplmentedError


class CompositeConfig(Config):

    def load(self, obj):
        from ..model import get_configs
        for config in get_configs(self):
            yield from config.load(obj)


class SelfConfig(Config):
    """
    This config simply provides access to the object associated with the 
    parameter in question.  By using callable keys, you can access any 
    attribute on the object.  If the object also happens to implement 
    `__getitem__()`, it will be used to lookup string keys.

    Example:

    >>> from appcli import Key, SelfConfig, param
    >>> class MyApp:
    ...     __config__ = [SelfConfig()]
    ...     
    ...     def _helper(self):
    ...         return 42
    ...
    ...     x = param(
    ...             Key(SelfConfig, _helper),
    ...     )
    ...     
    ...
    >>> app = MyApp()
    >>> app.x
    42
    """

    def load(self, obj):
        yield Layer(
                values=obj,
                location=_guess_module_path(obj),
        )


class AttrConfig(Config):
    """
    Read parameters from another attribute of the object.
    """

    def __init__(self, attr, f=lambda obj, x: x):
        self.attr = attr
        self.func = f

    def load(self, obj):

        @dict_like(AttributeError)
        def getter(key):
            x = getattr(obj, self.attr)
            x = self.func(obj, x)
            return lookup(x, key)

        yield Layer(
                values=getter,
                location=_guess_module_path(obj),
        )


class CallbackConfig(Config):

    def __init__(self, callback, *raises, location=None):
        self.callback = callback
        self.raises = raises
        self.location = location

    def load(self, obj):
        location = self.location or 'callback'
        if callable(location):
            location = location(obj)

        yield Layer(
                values=dict_like(*self.raises)(self.callback),
                location=location
        )


class DefaultConfig(Config):

    def __init__(self, **kwargs):
        self.dict = kwargs
        frame = inspect.stack()[1]
        self.location = f'{frame.filename}:{frame.lineno}'

    def load(self, obj):
        yield Layer(
                values=self.dict,
                location=self.location,
        )


class EnvironmentConfig(Config):

    def load(self, obj):
        yield Layer(
                values=os.environ,
                location="environment",
        )


class ArgparseConfig(Config):
    autoload = False

    def __init__(self, parser_getter=lambda self: self.get_argparse()):
        self.parser_getter = parser_getter

    def load(self, obj):
        import docopt

        parser = self.get_parser(obj)
        args = parser.parse_args()

        yield Layer(
                values=vars(args),
                location='command line',
        )

    def get_parser(self, obj):
        # Might make sense to try caching the parser in the given object.
        return self.parser_getter(obj)

    def get_usage(self, obj):
        return self.get_parser(obj).format_help()

    def get_brief(self, obj):
        return self.get_parser(obj).description


class DocoptConfig(Config):
    autoload = False

    def __init__(self,
            *,
            usage_getter=lambda self: self.__doc__,
            usage_io=sys.stdout,
            help=True,
            version=None,
            options_first=False,
        ):
        self.usage_getter = usage_getter
        self.usage_io = usage_io
        self.help = help
        self.version = version
        self.options_first = options_first

    def load(self, obj):
        import sys, docopt, contextlib

        with contextlib.redirect_stdout(self.get_usage_io(obj)):
            args = docopt.docopt(
                    self.get_usage(obj),
                    help=self.help,
                    version=self.get_version(obj),
                    options_first=self.options_first,
            )

        # If not specified:
        # - options with arguments will be None.
        # - options without arguments (i.e. flags) will be False.
        # - variable-number positional arguments (i.e. [<x>...]) will be []
        not_specified = [None, False, []]
        args = {k: v for k, v in args.items() if v not in not_specified}

        yield Layer(
                values=args,
                location='command line',
        )

    def get_usage(self, obj):
        from mako.template import Template
        usage = self.usage_getter(obj)
        usage = dedent(usage)
        usage = Template(usage, strict_undefined=True).render(app=obj)
        usage = re.sub(r' *$', '', usage, flags=re.MULTILINE)
        return usage

    def get_usage_io(self, obj):
        return getattr(obj, 'usage_io', self.usage_io)

    def get_brief(self, obj):
        import re
        sections = re.split(
                '\n\n|usage:',
                self.get_usage(obj),
                flags=re.IGNORECASE,
        )
        return first(sections, '').replace('\n', ' ').strip()

    def get_version(self, obj):
        return getattr(obj, '__version__', self.version)


class AppDirsConfig(Config):

    def __init__(self, name=None, format=None, slug=None, author=None, version=None, schema=None,
            stem='conf'):
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
        for p in paths:
            file_config = config_cls(p, schema=self.schema)
            yield from file_config.load(obj)

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

    def __init__(self, path, schema=None):
        """
        path: can be an path, or a callable that takes the object as it's only 
        argument and returns a path.  The purpose of specifying a callable is 
        usually to read the path from an attribute of the object, e.g. ``lambda 
        self: self.path``
        """
        self._path = path
        self.schema = schema

    def get_path(self, obj):
        if callable(self._path):
            return Path(self._path(obj))
        else:
            return Path(self._path)

    def load(self, obj):
        path = self.get_path(obj)

        try:
            data = self._do_load(path)
        except FileNotFoundError:
            data = {}

        if callable(self.schema):
            data = self.schema(data)

        yield Layer(
                values=data,
                location=path,
        )

    def _do_load(self, path):
        raise NotImplementedError

class YamlConfig(FileConfig):
    suffixes = '.yml', '.yaml'

    def _do_load(self, path):
        import yaml
        with open(path) as f:
            return yaml.safe_load(f)


class TomlConfig(FileConfig):
    suffixes = '.toml',

    def _do_load(self, path):
        import toml
        return toml.load(path)


class NtConfig(FileConfig):
    suffixes = '.nt',

    def _do_load(self, path):
        import nestedtext as nt
        return nt.load(path)


def _guess_module_path(x):
    try:
        return inspect.getmodule(x).__file__
    except Exception:
        return '???'
