#!/usr/bin/env python3

import appcli
import pytest
import parametrize_from_file
import sys, shlex

from voluptuous import Schema
from schema_helpers import *

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
        schema=Schema({
            'obj': exec_obj,
            'layers': eval_layers,
        })
)
def test_default_composite_config(obj, layers):
    appcli.init(obj)
    assert list(appcli.model.iter_layers(obj)) == layers

@parametrize_from_file(
        schema=Schema({
            'obj': exec_obj,
            'expected': {str: eval},
        })
)
def test_attr_callback_config(obj, expected):
    for attr, value in expected.items():
        assert getattr(obj, attr) == value

@parametrize_from_file(
        schema=Schema({
            'obj': exec_obj,
            'usage': str,
            'brief': str,
            'argv': shlex.split,
            'layer': eval_layer,
        })
)
def test_argparse_docopt_config(monkeypatch, obj, usage, brief, argv, layer):
    # These attributes should be available even before init() is called.
    assert obj.usage == usage
    assert obj.brief == brief

    # Make sure the command-line isn't read until load() is called.
    monkeypatch.setattr(sys, 'argv', [])
    appcli.init(obj)

    monkeypatch.setattr(sys, 'argv', argv)
    appcli.load(obj)

    assert list(appcli.model.iter_layers(obj)) == [layer]

@parametrize_from_file(
        schema=Schema({
            'obj': exec_obj,
            'slug': eval,
            'author': eval,
            'version': eval,
            'files': {str: str},
            'layers': eval_layers,
        })
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
    assert list(appcli.model.iter_layers(obj)) == layers

@parametrize_from_file(
        schema=Schema({
            'config': eval_appcli,
            **error_or(
                name=str,
                config_cls=eval_appcli,
            ),
        })
)
def test_appdirs_config_get_name_and_config_cls(config, name, config_cls, error):
    with error:
        assert config.get_name_and_config_cls() == (name, config_cls)

@parametrize_from_file(
        schema=Schema({
            'obj': exec_obj,
            'files': Or({str: str}, empty_dict),
            'layer': eval_layer,
        })
)
def test_file_config(tmp_chdir, obj, files, layer):
    for name, content in files.items():
        path = tmp_chdir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    appcli.init(obj)
    assert list(appcli.model.iter_layers(obj)) == [layer]

@parametrize_from_file(
        schema=Schema({
            'f': lambda x: exec_appcli(x)['f'],
            Optional('raises', default=[]): [eval],
            'error': error,
        })
)
def test_not_found(f, raises, error):
    with error:
        g = appcli.not_found(*raises)(f)
        assert g(1) == 2

