import logging
import time

import httpx

log = logging.getLogger("fasalscan.weather")

_CACHE: dict[tuple[float, float], tuple[float, dict]] = {}
_TTL = 30 * 60
FALLBACK = {"temp_c": 22.0, "humidity": 50.0, "outlook_c": 22.0, "source": "default"}


async def get_weather(lat: float, lon: float) -> dict:
    key = (round(lat, 2), round(lon, 2))
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < _TTL:
        return hit[1]

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m",
        "daily": "temperature_2m_max,temperature_2m_min",
        "forecast_days": 4,
        "timezone": "auto",
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            r.raise_for_status()
            data = r.json()
        cur = data["current"]
        daily = data["daily"]
        means = [(a + b) / 2 for a, b in zip(daily["temperature_2m_max"], daily["temperature_2m_min"])]
        outlook = sum(means) / len(means)
        result = {
            "temp_c": round(float(cur["temperature_2m"]), 1),
            "humidity": round(float(cur["relative_humidity_2m"]), 0),
            # shelf life cares about the next few days, not just this minute
            "outlook_c": round(outlook, 1),
            "source": "open-meteo",
        }
    except (httpx.HTTPError, KeyError, ValueError, ZeroDivisionError) as exc:
        log.warning("Weather lookup failed: %s", exc)
        result = dict(FALLBACK)

    _CACHE[key] = (time.time(), result)
    return result
