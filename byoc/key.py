#!/usr/bin/env python3

from typing import Any

def jmes(expr: str) -> Any:
    from jmespath import compile
    return compile(expr).search

