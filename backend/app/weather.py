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


_UA = {"User-Agent": "FasalScan/0.1 github.com/NK0028/fasalscan nk420545@gmail.com"}


async def _open_meteo(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m",
        "daily": "temperature_2m_max,temperature_2m_min",
        "forecast_days": 4,
        "timezone": "auto",
    }
    r = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
    r.raise_for_status()
    data = r.json()
    cur, daily = data["current"], data["daily"]
    means = [
        (a + b) / 2
        for a, b in zip(daily["temperature_2m_max"], daily["temperature_2m_min"])
        if a is not None and b is not None
    ]
    now = float(cur["temperature_2m"])
    return {
        "temp_c": round(now, 1),
        "humidity": round(float(cur["relative_humidity_2m"]), 0),
        "outlook_c": round(sum(means) / len(means), 1) if means else round(now, 1),
        "source": "open-meteo",
    }


async def _met_no(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    """Norwegian Met Institute: free, no key, asks for an identifying User-Agent."""
    r = await client.get(
        "https://api.met.no/weatherapi/locationforecast/2.0/compact",
        params={"lat": round(lat, 3), "lon": round(lon, 3)},
    )
    r.raise_for_status()
    series = r.json()["properties"]["timeseries"]
    first = series[0]["data"]["instant"]["details"]
    temps = [p["data"]["instant"]["details"]["air_temperature"] for p in series[:96]]  # ~next 4 days
    return {
        "temp_c": round(float(first["air_temperature"]), 1),
        "humidity": round(float(first.get("relative_humidity", 55)), 0),
        "outlook_c": round(sum(temps) / len(temps), 1),
        "source": "met.no",
    }


async def get_weather(lat: float, lon: float) -> dict:
    key = (round(lat, 2), round(lon, 2))
    hit = _CACHE.get(key)
    if hit and time.time() < hit[0]:
        return hit[1]

    errors = []
    result = None
    async with httpx.AsyncClient(timeout=6, headers=_UA) as client:
        for fetch in (_open_meteo, _met_no):
            try:
                result = await fetch(client, lat, lon)
                break
            except (httpx.HTTPError, KeyError, ValueError, TypeError, IndexError, ZeroDivisionError) as exc:
                errors.append(f"{fetch.__name__}: {type(exc).__name__} {str(exc)[:120]}")
    if result:
        last_error["weather"] = "; ".join(errors) or None
        _CACHE[key] = (time.time() + _TTL, result)
    else:
        last_error["weather"] = "; ".join(errors)[:400]
        log.warning("Live weather failed, using seasonal average: %s", last_error["weather"])
        result = _seasonal()
        _CACHE[key] = (time.time() + _FAIL_TTL, result)
    return result
