import logging
import time
from datetime import datetime, timezone

import httpx

log = logging.getLogger("fasalscan.weather")

_CACHE: dict[tuple[float, float], tuple[float, dict]] = {}
_TTL = 30 * 60
_FAIL_TTL = 5 * 60  # retry live weather sooner after a failure
last_error: dict = {"weather": None}

# Approximate monthly mean temperature (°C) for the Swat valley, used when live
# weather can't be fetched so the shelf-life estimate still tracks the season.
SWAT_MONTHLY_MEAN_C = [6, 8, 13, 18, 23, 28, 28, 27, 24, 18, 12, 7]


def _seasonal() -> dict:
    month = datetime.now(timezone.utc).month
    t = float(SWAT_MONTHLY_MEAN_C[month - 1])
    return {"temp_c": t, "humidity": 55.0, "outlook_c": t, "source": "seasonal"}


async def get_weather(lat: float, lon: float) -> dict:
    key = (round(lat, 2), round(lon, 2))
    hit = _CACHE.get(key)
    if hit and time.time() < hit[0]:
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
        async with httpx.AsyncClient(timeout=6, headers={"User-Agent": "FasalScan/0.1 (+github.com/NK0028/fasalscan)"}) as client:
            r = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            r.raise_for_status()
            data = r.json()
        cur = data["current"]
        daily = data["daily"]
        means = [
            (a + b) / 2
            for a, b in zip(daily["temperature_2m_max"], daily["temperature_2m_min"])
            if a is not None and b is not None
        ]
        result = {
            "temp_c": round(float(cur["temperature_2m"]), 1),
            "humidity": round(float(cur["relative_humidity_2m"]), 0),
            # shelf life cares about the next few days, not just this minute
            "outlook_c": round(sum(means) / len(means), 1) if means else round(float(cur["temperature_2m"]), 1),
            "source": "open-meteo",
        }
        last_error["weather"] = None
        _CACHE[key] = (time.time() + _TTL, result)
    except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
        last_error["weather"] = f"{type(exc).__name__}: {exc}"[:300]
        log.warning("Weather lookup failed, using seasonal average: %s", last_error["weather"])
        result = _seasonal()
        _CACHE[key] = (time.time() + _FAIL_TTL, result)
    return result
