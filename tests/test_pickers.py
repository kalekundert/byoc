#!/usr/bin/env python3

import appcli
import parametrize_from_file

from appcli.model import UNSPECIFIED
from appcli.errors import Log
from param_helpers import *

class DummyObj:
    pass

@parametrize_from_file(
        schema=Schema({
            Optional('obj', default='class DummyObj: __config__ = []'): str,
            Optional('param', default=''): str,
            'getters': empty_ok([str]),
            Optional('default', default=''): str,
            'expected': empty_ok([with_py.eval]),
            'log': empty_ok([str]),
        })
)
def test_values_iter(obj, param, getters, default, expected, log):
    with_obj = with_appcli.exec(obj)
    obj = get_obj(with_obj)
    param = find_param(obj, param)
    getters = [with_obj.eval(x) for x in getters]
    default = with_py.eval(default) if default else UNSPECIFIED

    appcli.init(obj)

    bound_getters = [
            x.bind(obj, param)
            for x in getters
    ]

    values = appcli.pickers.ValuesIter(bound_getters, default, Log())
    assert list(values) == expected
    assert values.log._err.info_strs == log

