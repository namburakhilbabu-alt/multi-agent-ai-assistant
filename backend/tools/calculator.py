"""A safe arithmetic evaluator exposed as a tool."""

from __future__ import annotations

import ast
import operator

from .base import tool

# Only these operators are allowed — no names, calls, or attribute access.
_OPERATORS = {
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


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("only numbers are allowed")
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported expression")


@tool(
    description="Evaluate a basic arithmetic expression using +, -, *, /, ** and %. "
    "Use this for any calculation.",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The arithmetic expression to evaluate.",
            }
        },
        "required": ["expression"],
    },
)
def calculator(expression: str) -> str:
    result = _eval(ast.parse(expression, mode="eval").body)
    # Present whole numbers cleanly (12.0 -> 12).
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return f"{expression} = {result}"
