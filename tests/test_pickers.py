#!/usr/bin/env python3

import appcli
import parametrize_from_file

from appcli.model import UNSPECIFIED
from appcli.errors import Log
from schema_helpers import *

class DummyObj:
    pass


@parametrize_from_file(
        schema=Schema({
            Optional('obj', default='class DummyObj: __config__ = []'): str,
            Optional('param', default=''): str,
            'getters': Or([str], empty_list),
            Optional('default', default=''): str,
            'expected': Or([eval], empty_list),
            'log': Or([str], empty_list),
        })
)
def test_values_iter(obj, param, getters, default, expected, log):
    globals = {}
    obj = exec_obj(obj, globals)
    param = find_param(obj, param)
    getters = [eval_appcli(x, globals) for x in getters]
    default = eval(default) if default else UNSPECIFIED

    appcli.init(obj)

    bound_getters = [
            x.bind(obj, param)
            for x in getters
    ]

    values = appcli.pickers.ValuesIter(bound_getters, default, Log())
    assert list(values) == expected
    assert values.log._err.info_strs == log

