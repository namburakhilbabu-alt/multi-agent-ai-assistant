"""Unit tests for the tools — they run without a model or network.

    pip install pytest && pytest
"""

from backend.tools import calculator, convert_units, search_knowledge_base
from backend.tools.calculator import _eval
import ast


def _calc(expr: str) -> str:
    return calculator.run(expression=expr)


def test_calculator_basic():
    assert _calc("(1200 * 1.18) / 12") == "(1200 * 1.18) / 12 = 118"
    assert _calc("2 ** 10") == "2 ** 10 = 1024"


def test_calculator_is_safe():
    # Names, calls and attribute access must be rejected, not executed.
    assert "error" in _calc("__import__('os').system('echo hi')").lower()


def test_convert_units_length_and_aliases():
    # Full unit names (as a model might emit) are normalised to symbols.
    assert convert_units.run(value=5, from_unit="miles", to_unit="kilometers") == \
        "5 miles = 8.0467 kilometers"


def test_convert_units_temperature():
    assert convert_units.run(value=100, from_unit="c", to_unit="f") == "100 c = 212.0 f"


def test_convert_units_incompatible():
    result = convert_units.run(value=1, from_unit="kg", to_unit="m")
    assert "cannot convert" in result.lower()


def test_knowledge_base_finds_agents():
    result = search_knowledge_base.run(query="what agents does Maestro have")
    assert "Math Agent" in result


def test_tool_spec_shape():
    spec = calculator.spec
    assert spec["type"] == "function"
    assert spec["function"]["name"] == "calculator"
    assert "expression" in spec["function"]["parameters"]["properties"]
