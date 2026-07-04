"""Unit conversion tool exposed as a LangChain tool."""

from __future__ import annotations

from langchain_core.tools import tool

_LENGTH = {"mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0,
           "in": 0.0254, "ft": 0.3048, "mi": 1609.34}
_MASS = {"mg": 0.001, "g": 1.0, "kg": 1000.0, "lb": 453.592, "oz": 28.3495}

_ALIASES = {
    "millimeter": "mm", "millimetre": "mm", "millimeters": "mm", "millimetres": "mm",
    "centimeter": "cm", "centimetre": "cm", "centimeters": "cm", "centimetres": "cm",
    "meter": "m", "metre": "m", "meters": "m", "metres": "m",
    "kilometer": "km", "kilometre": "km", "kilometers": "km", "kilometres": "km",
    "inch": "in", "inches": "in", "foot": "ft", "feet": "ft",
    "mile": "mi", "miles": "mi",
    "milligram": "mg", "milligrams": "mg", "gram": "g", "grams": "g",
    "kilogram": "kg", "kilograms": "kg", "pound": "lb", "pounds": "lb", "lbs": "lb",
    "ounce": "oz", "ounces": "oz",
    "celsius": "c", "centigrade": "c", "fahrenheit": "f", "kelvin": "k",
}


def _canon(unit: str) -> str:
    u = unit.strip().lower()
    return _ALIASES.get(u, u)


def _convert_temp(value: float, src: str, dst: str) -> float:
    celsius = {"c": value, "f": (value - 32) / 1.8, "k": value - 273.15}[src]
    return {"c": celsius, "f": celsius * 1.8 + 32, "k": celsius + 273.15}[dst]


@tool
def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """Convert a value between units of length (mm, cm, m, km, in, ft, mi), mass (mg, g, kg, lb, oz) or temperature (c, f, k)."""
    try:
        src, dst = _canon(from_unit), _canon(to_unit)
        if src in _LENGTH and dst in _LENGTH:
            result = value * _LENGTH[src] / _LENGTH[dst]
        elif src in _MASS and dst in _MASS:
            result = value * _MASS[src] / _MASS[dst]
        elif src in "cfk" and dst in "cfk":
            result = _convert_temp(value, src, dst)
        else:
            return f"Cannot convert from '{from_unit}' to '{to_unit}' (incompatible units)."
        return f"{value} {from_unit} = {round(result, 4)} {to_unit}"
    except Exception as exc:
        return f"Conversion error: {exc}"
