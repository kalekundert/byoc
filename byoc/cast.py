#!/usr/bin/env python3

import sys
import inspect

from .errors import Error
from more_itertools import first
from typing import Union

class Context:

    def __init__(self, value, meta, obj):
        self.value = value
        self.meta = meta
        self.obj = obj

def call_with_context(f, context):
    try:
        sig = inspect.signature(f)
        param = first(sig.parameters.values())

    except ValueError:
        pass

    else:
        if param.annotation is Context:
            return f(context)

    return f(context.value)


def arithmetic_eval(expr: str) -> Union[int, float]:
    """\
    Evaluate the given arithmetic expression.

    Arguments:
        expr:
            The expression to evaluate.  The syntax is identical to python, but 
            only `int` literals, `float` literals, binary operators (except 
            left/right shift, bitwise and/or/xor, and matrix multiplication),
            and unary operators are allowed.

    Returns:
        The value of the given expression.

    Raises:
        SyntaxError: If *expr* cannot be parsed for any reason.
        TypeError: If the *expr* argument is not a string.
        ZeroDivisionError: If *expr* divides by zero.

    It is safe to call this function on untrusted input, as there is no way to 
    construct an expression that will execute arbitrary code.
    """
    import ast, operator

    operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,

            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
    }

    def eval_node(node):

        if sys.version_info[:2] < (3, 8):
            if isinstance(node, ast.Num):
                return node.n

        else:
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value
                else:
                    err = ArithmeticError(expr, non_number=node.value)
                    err.blame += "{non_number!r} is not a number"
                    raise err

        if isinstance(node, ast.BinOp):
            try:
                op = operators[type(node.op)]
            except KeyError:
                err = ArithmeticError(expr, op=node.op)
                err.blame += "the {op.__class__.__name__} operator is not supported"
                raise err

            left = eval_node(node.left)
            right = eval_node(node.right)
            return op(left, right)

        if isinstance(node, ast.UnaryOp):
            assert type(node.op) in operators
            op = operators[type(node.op)]
            value = eval_node(node.operand)
            return op(value)

        raise ArithmeticError(expr)

    root = ast.parse(expr.lstrip(" \t"), mode='eval')
    return eval_node(root.body)

def int_eval(expr: str) -> int:
    """\
    Same as `arithmetic_eval()`, but convert the result to `int`.
    """
    return int(arithmetic_eval(expr))

def float_eval(expr: str) -> float:
    """\
    Same as `arithmetic_eval()`, but convert the result to `float`.
    """
    return float(arithmetic_eval(expr))

class ArithmeticError(Error, SyntaxError):

    def __init__(self, expr, **kwargs):
        super().__init__(expr=expr, **kwargs)
        self.brief = "unable to evaluate arithmetic expression"
        self.info += "expression: {expr}"


