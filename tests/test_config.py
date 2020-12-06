#!/usr/bin/env python3

import appcli
import pytest
import parametrize_from_file
import sys, shlex

from schema import Use
from schema_helpers import *
from test_model import LayerWrapper

@pytest.fixture
def tmp_chdir(tmp_path):
    import os
    try:
        cwd = os.getcwd()
        os.chdir(tmp_path)
        yield tmp_path
    finally:
        os.chdir(cwd)


@parametrize_from_file(
        schema={
            'config': Use(exec_config),
            'key_group': Use(eval),
            'cast_group': Use(eval),
            'require_explicit_load': Use(eval),
        }
)
def test_config(config, key_group, cast_group, require_explicit_load):
    assert config.key_group == key_group
    assert config.cast_group == cast_group
    assert config.require_explicit_load == require_explicit_load

@parametrize_from_file(
        schema={
            'obj': Use(exec_obj),
            'layers': [Use(eval_appcli)],
        }
)
def test_dict_config(obj, layers):
    appcli.init(obj)
    assert appcli.model.get_layers(obj) == [LayerWrapper(x) for x in layers]

@parametrize_from_file(
        schema={
            'obj': Use(exec_obj),
            'expected': {str: Use(eval)},
        }
)
def test_attr_config(obj, expected):
    for attr, value in expected.items():
        assert getattr(obj, attr) == value

@parametrize_from_file(
        schema={
            'obj': Use(exec_obj),
            'usage': str,
            'brief': str,
            'argv': Use(shlex.split),
            'layers': [Use(eval_appcli)],
        }
)
def test_docopt_config(monkeypatch, obj, usage, brief, argv, layers):
    # These attributes should be available even before init() is called.
    assert obj.usage == usage
    assert obj.brief == brief

    # Make sure the command-line isn't read until load() is called.
    monkeypatch.setattr(sys, 'argv', [])
    appcli.init(obj)

    monkeypatch.setattr(sys, 'argv', argv)
    appcli.load(obj)

    assert appcli.model.get_layers(obj) == [LayerWrapper(x) for x in layers]

@parametrize_from_file(
        schema={
            'obj': Use(exec_obj),
            'slug': Use(eval),
            'author': Use(eval),
            'version': Use(eval),
            'files': {str: str},
            'layers': Use(eval_layers),
        }
)
def test_appdirs_config(tmp_chdir, monkeypatch, obj, slug, author, version, files, layers):
    import appdirs

    class AppDirs:

        def __init__(self, slug, author, version):
            self.slug = slug
            self.author = author
            self.version = version

            self.user_config_dir = 'user'
            self.site_config_dir = 'site'

    monkeypatch.setattr(appdirs, 'AppDirs', AppDirs)

    for name, content in files.items():
        path = tmp_chdir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    assert obj.dirs.slug == slug
    assert obj.dirs.author == author
    assert obj.dirs.version == version

    appcli.init(obj)
    assert appcli.model.get_layers(obj) == layers

@parametrize_from_file(
        schema={
            'config': Use(eval_appcli),
            **error_or(
                name=str,
                config_cls=Use(eval_appcli),
            ),
        }
)
def test_appdirs_config_get_name_and_config_cls(config, name, config_cls, error):
    with error:
        assert config.get_name_and_config_cls() == (name, config_cls)

@parametrize_from_file(
        schema={
            'obj': Use(exec_obj),
            'files': {str: str},
            'layer': Use(eval_layer),
        }
)
def test_file_config(tmp_chdir, obj, files, layer):
    for name, content in files.items():
        path = tmp_chdir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    appcli.init(obj)
    assert appcli.model.get_layers(obj) == [layer]

@parametrize_from_file(
        schema={
            'f': Use(lambda x: exec_appcli(x)['f']),
            Optional('raises', default=[]): [Use(eval)],
            'error': Use(error),
        }
)
def test_not_found(f, raises, error):
    with error:
        g = appcli.not_found(*raises)(f)
        assert g(1) == 2

