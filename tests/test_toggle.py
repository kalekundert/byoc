#!/usr/bin/env python3

import byoc
import parametrize_from_file
from voluptuous import Schema
from param_helpers import *

@parametrize_from_file(
        schema=Schema({
            'layers': [{
                'value': with_py.eval,
                'toggle': with_py.eval,
            }],
            **with_byoc.error_or({
                'expected': with_py.eval,
            })
        }),
)
def test_toggle(layers, expected, error):

    class BaseConfig(byoc.Config):

        def load(self):
            yield byoc.DictLayer(
                    values={'flag': self.value},
                    location=self.location,
            )

    configs = []
    toggles = set()
    keys = []

    for i, layer in enumerate(layers):

        class DerivedConfig(BaseConfig):
            value = layer['value']
            location = str(i+1)

        configs.append(DerivedConfig)
        keys.append(byoc.Key(DerivedConfig, toggle=layer['toggle']))

    class DummyObj:
        __config__ = configs

        flag = byoc.toggle_param(*keys)

    obj = DummyObj()
    with error:
        assert obj.flag == expected




