#!/usr/bin/env python3

import byoc
import pytest

def test_app():

    class DummyConfig(byoc.Config):
        def load(self):
            yield byoc.DictLayer({'x': 1})

    class DummyApp(byoc.App):
        __config__ = [DummyConfig]
        x = byoc.param()

        def __bareinit__(self):
            self.y = 0

        def __init__(self, x):
            self.x = x

    app = DummyApp(2)
    assert app.x == 2
    assert app.y == 0

    app = DummyApp.from_bare()
    assert app.x == 1
    assert app.y == 0

def test_app_entrypoint():
    d = {}

    class DummyApp(byoc.App):

        def __bareinit__(self):
            self.x = 1

        def __init__(self, x):
            self.x = x

        def main(self):
            d['x'] = self.x

    DummyApp.entry_point()
    assert d == {'x': 1}

    DummyApp(2).main()
    assert d == {'x': 2}

def test_app_bareinit_defined():

    class DummyApp(byoc.App):

        def __init__(self, x):
            self.x = x

    app = DummyApp.from_bare()
    assert not hasattr(app, 'x')

def test_app_load_reload():
    d = {'x': 1}

    class DummyConfig(byoc.Config):
        autoload = False
        def load(self):
            yield byoc.DictLayer(d)

    class DummyApp(byoc.App):
        __config__ = [DummyConfig]
        x = byoc.param()

    app = DummyApp()

    with pytest.raises(byoc.NoValueFound):
        app.x

    app.load()
    assert app.x == 1

    d['x'] = 2
    assert app.x == 1

    app.reload()
    assert app.x == 2


    
