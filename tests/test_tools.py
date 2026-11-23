"""Unit tests for the tools — they run without a model or network.

    pip install pytest && pytest
"""

from langchain_core.utils.function_calling import convert_to_openai_tool

from backend.tools import calculator, convert_units, search_knowledge_base


def _calc(expr: str) -> str:
    return calculator.invoke({"expression": expr})


def _convert(value, from_unit: str, to_unit: str) -> str:
    return convert_units.invoke({"value": value, "from_unit": from_unit, "to_unit": to_unit})


def test_calculator_basic():
    assert _calc("(1200 * 1.18) / 12") == "(1200 * 1.18) / 12 = 118"
    assert _calc("2 ** 10") == "2 ** 10 = 1024"


def test_calculator_is_safe():
    # Names, calls and attribute access must be rejected, not executed.
    assert "error" in _calc("__import__('os').system('echo hi')").lower()


def test_convert_units_length_and_aliases():
    # Full unit names (as a model might emit) are normalised to symbols.
    assert _convert(5, "miles", "kilometers") == "5 miles = 8.0467 kilometers"


def test_convert_units_temperature():
    assert _convert(100, "c", "f") == "100 c = 212.0 f"


def test_convert_units_incompatible():
    assert "cannot convert" in _convert(1, "kg", "m").lower()


def test_knowledge_base_finds_agents():
    result = search_knowledge_base.invoke({"query": "what agents does Maestro have"})
    assert "Math Agent" in result


def test_tool_spec_shape():
    spec = convert_to_openai_tool(calculator)
    assert spec["type"] == "function"
    assert spec["function"]["name"] == "calculator"
    assert "expression" in spec["function"]["parameters"]["properties"]
