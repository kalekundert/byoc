#!/usr/bin/env python3

import appcli
import pytest
import parametrize_from_file
import sys, os, shlex

from unittest import mock
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
    assert collect_layers(obj) == layers

@parametrize_from_file(
        schema=Schema({
            'obj': exec_obj,
            'expected': {str: eval},
        })
)
def test_self_attr_callback_config(obj, expected):
    for attr, value in expected.items():
        assert getattr(obj, attr) == value

@parametrize_from_file(
        schema=Schema({
            'obj': exec_obj,
            'usage': str,
            'brief': str,
            'invocations': [{
                'argv': shlex.split,
                'layer': eval_layer,
            }],
        })
)
def test_argparse_docopt_config(monkeypatch, obj, usage, brief, invocations):
    from copy import copy

    for invocation in invocations:
        print(invocation)

        test_obj = copy(obj)
        test_argv = invocation['argv']
        test_layer = invocation['layer']

        # Clear `sys.argv` so that if the command-line is accessed prematurely, 
        # e.g. in `init()` rather than `load()`, an error is raised.  Note that 
        # `sys.argv[0]` needs to be present, because `argparse` checks this 
        # when generating usage text.
        monkeypatch.setattr(sys, 'argv', ['app'])

        # These attributes should be available even before `init()` is called.  
        # Note that accessing these attributes may trigger `init()`, e.g. if 
        # the usage text contains default values based on parameters.
        assert test_obj.usage == usage
        assert test_obj.brief == brief

        # Make sure that calling `init()` (if it wasn't implicitly called 
        # above) doesn't cause the command line to be read.
        appcli.init(test_obj)

        monkeypatch.setattr(sys, 'argv', test_argv)
        appcli.load(test_obj)

        assert collect_layers(test_obj) == {0: [test_layer]}

@mock.patch.dict(os.environ, {"x": "1"})
def test_environment_config():
    class DummyObj:
        __config__ = [
                appcli.EnvironmentConfig(),
        ]
        x = appcli.param()

    obj = DummyObj()
    assert obj.x == "1"

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
    assert collect_layers(obj) == layers

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
    assert collect_layers(obj) == {0: [layer]}

@parametrize_from_file
def test_on_load(prepare, load, expected):

    class DummyConfig(appcli.Config):
        def load(self, obj):
            yield appcli.Layer(values={}, location=self.__class__.__name__)

    class A(DummyConfig):
        pass

    class A1(A):
        pass

    class A2(A):
        pass

    class B(DummyConfig):
        autoload = False

    class B1(B):
        pass

    class B2(B):
        pass

    class DummyObj:
        __config__ = [A1(), A2(), B1(), B2()]

        def __init__(self):
            self.calls = set()

        @appcli.on_load
        def on_default(self):
            self.calls.add('default')

        @appcli.on_load(DummyConfig)
        def on_dummy_config(self):
            self.calls.add('DummyConfig')

        @appcli.on_load(A)
        def on_a(self):
            self.calls.add('A')

        @appcli.on_load(A1)
        def on_a1(self):
            self.calls.add('A1')

        @appcli.on_load(A2)
        def on_a2(self):
            self.calls.add('A2')

        @appcli.on_load(B)
        def on_b(self):
            self.calls.add('B')

        @appcli.on_load(B1)
        def on_b1(self):
            self.calls.add('B1')

        @appcli.on_load(B2)
        def on_b2(self):
            self.calls.add('B2')

    obj = DummyObj()

    exec_appcli(prepare, **locals())
    obj.calls = set()

    exec_appcli(load, **locals())
    assert obj.calls == set(expected or [])

def test_on_load_inheritance():

    class DummyConfig(appcli.Config):
        def load(self, obj):
            yield appcli.Layer(values={}, location='a')

    class P:
        __config__ = [DummyConfig()]

        def __init__(self):
            self.calls = set()

        @appcli.on_load
        def a(self):
            self.calls.add('P/a')

        @appcli.on_load
        def b(self):
            self.calls.add('P/b')

        @appcli.on_load
        def c(self):
            self.calls.add('P/c')

    class F1(P):

        @appcli.on_load
        def a(self):
            self.calls.add('F1/a')

        @appcli.on_load
        def b(self):
            self.calls.add('F1/b')

    class F2(F1):

        @appcli.on_load
        def a(self):
            self.calls.add('F2/a')

    p = P()
    f1 = F1()
    f2 = F2()

    appcli.init(p)
    appcli.init(f1)
    appcli.init(f2)

    assert p.calls  == { 'P/a',  'P/b', 'P/c'}
    assert f1.calls == {'F1/a', 'F1/b', 'P/c'}
    assert f2.calls == {'F2/a', 'F1/b', 'P/c'}

@parametrize_from_file(
        schema=Schema({
            'f': lambda x: exec_appcli(x)['f'],
            Optional('raises', default=[]): [eval],
            **error_or(
                x=eval,
                expected=eval,
            ),
        })
)
@pytest.mark.parametrize(
        'factory', [
            pytest.param(
                lambda f, raises: appcli.dict_like(*raises)(f),
                id='decorator',
            ),
            pytest.param(
                lambda f, raises: appcli.dict_like(f, *raises),
                id='constructor',
            ),
        ]
)
def test_dict_like(factory, f, raises, x, expected, error):
    with error:
        g = factory(f, raises)
        assert g[x] == expected

