#!/usr/bin/env python3

import appcli
import parametrize_from_file
from voluptuous import Schema
from param_helpers import *

@parametrize_from_file(
        schema=Schema({
            'layers': [{
                'value': with_py.eval,
                'toggle': with_py.eval,
            }],
            **with_appcli.error_or({
                'expected': with_py.eval,
            })
        }),
)
def test_toggle(layers, expected, error):

    class BaseConfig(appcli.Config):

        def load(self):
            yield appcli.DictLayer(
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
        keys.append(appcli.Key(DerivedConfig, toggle=layer['toggle']))

    class DummyObj:
        __config__ = configs

        flag = appcli.toggle_param(*keys)

    obj = DummyObj()
    with error:
        assert obj.flag == expected




