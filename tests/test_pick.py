#!/usr/bin/env python3

import byoc
import parametrize_from_file

from byoc.model import UNSPECIFIED
from byoc.errors import Log
from param_helpers import *

class DummyObj:
    pass

class DummyValueIter(byoc.pick.ValuesIter):

    def __init__(self, values):
        self._with_meta = values
        self.log = Log()

    @property
    def with_meta(self):
        return self._with_meta

@parametrize_from_file(
        schema=Schema({
            Optional('obj', default='class DummyObj: pass'): str,
            Optional('param', default=''): str,
            'getters': empty_ok([str]),
            Optional('default', default=''): str,
            'expected': empty_ok([with_py.eval]),
            'log': empty_ok([str]),
        })
)
def test_values_iter(obj, param, getters, default, expected, log, monkeypatch):
    monkeypatch.setenv('BYOC_VERBOSE', '1')

    with_obj = with_byoc.exec(obj)
    obj = get_obj(with_obj)
    param = find_param(obj, param)
    getters = [with_obj.eval(x) for x in getters]
    default = with_py.eval(default) if default else UNSPECIFIED

    byoc.init(obj)

    bound_getters = [
            x.bind(obj, param)
            for x in getters
    ]

    values = byoc.pick.ValuesIter(bound_getters, default, Log())
    assert list(values) == expected
    assert values.log.message_strs == log

@parametrize_from_file(
        schema=Schema({
            'pick_func': with_byoc.eval,
            'values_iter': lambda x: DummyValueIter(with_py.eval(x)),
            **with_byoc.error_or({
                'expected': {
                    'value': with_py.eval,
                    'meta': with_py.eval,
                },
            }),
        }),
)
def test_pick_functions(pick_func, values_iter, expected, error):
    with error:
        assert pick_func(values_iter) == expected['value']
        assert values_iter.meta == expected['meta']
