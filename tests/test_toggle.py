#!/usr/bin/env python3

import appcli
import parametrize_from_file
from voluptuous import Schema
from schema_helpers import *

@parametrize_from_file(
        schema=Schema({
            'layers': [{
                'value': eval,
                'toggle': eval,
            }],
            **error_or(
                expected=eval,
            )
        }),
)
def test_toggle(layers, expected, error):

    class BaseConfig(appcli.Config):

        def load(self, obj):
            yield appcli.Layer(
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

        configs.append(DerivedConfig())
        keys.append(appcli.Key(DerivedConfig, toggle=layer['toggle']))

    class DummyObj:
        __config__ = configs

        flag = appcli.toggle_param(*keys)

    obj = DummyObj()
    with error:
        assert obj.flag == expected




