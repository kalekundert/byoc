#!/usr/bin/env python3

import byoc
import parametrize_from_file
from param_helpers import *

@parametrize_from_file(
        schema=Schema({
            'obj': with_byoc.exec(get=get_obj, defer=True),
            'expected': {str: eval_meta},
        }),
)
def test_meta_view(obj, expected):
    obj = obj()
    for param, meta in expected.items():
        assert getattr(obj.meta, param) == meta

def test_meta_repr():
    from byoc.meta import GetterMeta, LayerMeta
    from unittest.mock import Mock

    meta = GetterMeta(Mock())
    assert repr(meta) == 'GetterMeta()'

    layer = Mock()
    layer.location = '/path/to/file'
    meta = LayerMeta(Mock(), layer)
    assert repr(meta) == "LayerMeta(location='/path/to/file')"
