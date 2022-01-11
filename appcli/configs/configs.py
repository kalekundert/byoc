#!/usr/bin/env python3

import sys, os, re, inspect, autoprop

from .layers import DictLayer, dict_like
from ..utils import lookup, first_specified
from ..errors import ConfigError
from pathlib import Path
from textwrap import dedent
from more_itertools import one, first
from collections.abc import Iterable

class Config:
    autoload = True

    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    @classmethod
    def setup(cls, *args, **kwargs):
        return lambda obj: cls(obj, *args, **kwargs)

    def load(self):
        raise NotImplmentedError

class EnvironmentConfig(Config):

    def load(self):
        yield DictLayer(
                values=os.environ,
                location="environment",
        )


@autoprop
class ArgparseConfig(Config):
    autoload = False
    parser_getter = lambda obj: obj.get_argparse()
    schema = None

    def __init__(self, obj, **kwargs):
        super().__init__(obj)

        self.parser_getter = kwargs.get(
                'parser_getter', unbind_method(self.parser_getter))
        self.schema = kwargs.get(
                'schema', self.schema)

    def load(self):
        args = self.parser.parse_args()
        yield DictLayer(
                values=vars(args),
                schema=self.schema,
                location='command line',
        )

    def get_parser(self):
        # Might make sense to cache the parser.
        return self.parser_getter(self.obj)

    def get_usage(self):
        return self.parser.format_help()

    def get_brief(self):
        return self.parser.description


@autoprop
class DocoptConfig(Config):
    autoload = False
    usage_getter = lambda obj: obj.__doc__
    version_getter = lambda obj: getattr(obj, '__version__')
    usage_io_getter = lambda obj: sys.stdout
    include_help = True
    include_version = None
    options_first = False
    schema = None

    def __init__(self, obj, **kwargs):
        super().__init__(obj)

        self.usage_getter = kwargs.get(
                'usage_getter', unbind_method(self.usage_getter))
        self.version_getter = kwargs.get(
                'version_getter', unbind_method(self.version_getter))
        self.usage_io_getter = kwargs.get(
                'usage_io_getter', unbind_method(self.usage_io_getter))
        self.include_help = kwargs.get(
                'include_help', self.include_help)
        self.include_version = kwargs.get(
                'include_version', self.include_version)
        self.options_first = kwargs.get(
                'options_first', self.options_first)
        self.schema = kwargs.get(
                'schema', unbind_method(self.schema))

    def load(self):
        import sys, docopt, contextlib

        with contextlib.redirect_stdout(self.usage_io):
            args = docopt.docopt(
                    self.usage,
                    help=self.include_help,
                    version=self.version,
                    options_first=self.options_first,
            )

        # If not specified:
        # - options with arguments will be None.
        # - options without arguments (i.e. flags) will be False.
        # - variable-number positional arguments (i.e. [<x>...]) will be []
        not_specified = [None, False, []]
        args = {k: v for k, v in args.items() if v not in not_specified}

        yield DictLayer(
                values=args,
                schema=self.schema,
                location='command line',
        )

    def get_usage(self):
        from mako.template import Template

        usage = self.usage_getter(self.obj)
        usage = dedent(usage)
        usage = Template(usage, strict_undefined=True).render(app=self.obj)

        # Trailing whitespace can cause unnecessary line wrapping.
        usage = re.sub(r' *$', '', usage, flags=re.MULTILINE)

        return usage

    def get_usage_io(self):
        return self.usage_io_getter(self.obj)

    def get_brief(self):
        import re
        sections = re.split(
                '\n\n|usage:',
                self.usage,
                flags=re.IGNORECASE,
        )
        return first(sections, '').replace('\n', ' ').strip()

    def get_version(self):
        return self.include_version and self.version_getter(self.obj)


@autoprop
class AppDirsConfig(Config):
    name = None
    config_cls = None
    slug = None
    author = None
    version = None
    schema = None
    root_key = None
    stem = 'conf'

    def load(self):
        for path, config_cls in self.config_map.items():
            yield from config_cls.load_from_path(
                    path=path, schema=self.schema, root_key=self.root_key,
            )

    def get_name_and_config_cls(self):
        if not self.name and not self.config_cls:
            raise ConfigError("must specify `AppDirsConfig.name` or `AppDirsConfig.config_cls`")

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

    def get_dirs(self):
        from appdirs import AppDirs
        slug = self.slug or self.obj.__class__.__name__.lower()
        return AppDirs(slug, self.author, version=self.version)

    def get_config_map(self):
        dirs = self.dirs
        name, config_cls = self.name_and_config_cls
        return {
                Path(dirs.user_config_dir) / name: config_cls,
                Path(dirs.site_config_dir) / name: config_cls,
        }

    def get_config_paths(self):
        return self.config_map.keys()
        

@autoprop
class FileConfig(Config):
    path_getter = lambda obj: obj.path
    schema = None
    root_key = None

    def __init__(self, obj, path=None, *, path_getter=None, schema=None, root_key=None):
        super().__init__(obj)
        self._path = path
        self._path_getter = path_getter or unbind_method(self.path_getter)
        self.schema = schema or self.schema
        self.root_key = root_key or self.root_key

    def get_paths(self):
        p = self._path or self._path_getter(self.obj)

        if isinstance(p, Iterable) and not isinstance(p, str):
            return [Path(pi) for pi in p]
        else:
            return [Path(p)]

    def load(self):
        for path in self.paths:
            yield from self.load_from_path(
                    path=path,
                    schema=self.schema,
                    root_key=self.root_key,
            )

    @classmethod
    def load_from_path(cls, path, *, schema=None, root_key=None):
        try:
            data = cls._do_load(path)
        except FileNotFoundError:
            data = {}

        yield DictLayer(
                values=data,
                location=path,
                schema=schema,
                root_key=root_key,
        )

    @staticmethod
    def _do_load(path):
        raise NotImplementedError

class YamlConfig(FileConfig):
    suffixes = '.yml', '.yaml'

    @staticmethod
    def _do_load(path):
        import yaml
        with open(path) as f:
            return yaml.safe_load(f)


class TomlConfig(FileConfig):
    suffixes = '.toml',

    @staticmethod
    def _do_load(path):
        import tomli
        with open(path, 'rb') as f:
            return tomli.load(f)


class NtConfig(FileConfig):
    suffixes = '.nt',

    @staticmethod
    def _do_load(path):
        import nestedtext as nt
        return nt.load(path)

def unbind_method(f):
    return getattr(f, '__func__', f)
