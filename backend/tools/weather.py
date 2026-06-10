"""Live weather lookup via the free, key-less Open-Meteo API."""

from __future__ import annotations

import httpx

from .base import tool

_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST = "https://api.open-meteo.com/v1/forecast"

# Open-Meteo WMO weather codes -> human readable.
_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog", 51: "light drizzle", 53: "drizzle",
    55: "dense drizzle", 61: "slight rain", 63: "rain", 65: "heavy rain",
    71: "slight snow", 73: "snow", 75: "heavy snow", 80: "rain showers",
    81: "rain showers", 82: "violent rain showers", 95: "thunderstorm",
}


@tool(
    description="Get the current weather (temperature and conditions) for a city. "
    "Use this whenever the user asks about weather.",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name, e.g. 'Berlin'."}
        },
        "required": ["city"],
    },
)
def get_weather(city: str) -> str:
    with httpx.Client(timeout=15) as client:
        geo = client.get(_GEOCODE, params={"name": city, "count": 1}).json()
        results = geo.get("results")
        if not results:
            return f"Could not find a location named '{city}'."

        place = results[0]
        forecast = client.get(
            _FORECAST,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current_weather": True,
            },
        ).json()

    current = forecast.get("current_weather", {})
    conditions = _CODES.get(current.get("weathercode"), "unknown conditions")
    name = f"{place['name']}, {place.get('country', '')}".strip(", ")
    return (
        f"Weather in {name}: {current.get('temperature')}°C, {conditions}, "
        f"wind {current.get('windspeed')} km/h."
    )
