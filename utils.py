import re
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import dateparser
import zoneinfo
import requests

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import DATE_FMT
from config import (
    GEOCODER_NOMINATIM_BASE_URL,
    GEOCODER_NOMINATIM_USER_AGENT,
    GEOCODER_NOMINATIM_EMAIL,
)

LOCAL_TZ = zoneinfo.ZoneInfo("America/Toronto")

_geocode_cache: Dict[str, Tuple[float, float]] = {}


def parse_date(text: Optional[str]) -> Optional[str]:
    if not text:
        return None

    local_now = datetime.now(LOCAL_TZ).replace(tzinfo=None)

    def _parse(s: str, order: str):
        return dateparser.parse(
            s,
            settings={
                "RELATIVE_BASE": local_now,
                "PREFER_DATES_FROM": "future",
                "RETURN_AS_TIMEZONE_AWARE": False,
                "DATE_ORDER": order,
                "PREFER_DAY_OF_MONTH": "current",
            },
        )

    s = str(text)
    dt = _parse(s, "DMY") or _parse(s, "MDY")
    if not dt:
        return None

    user_has_year = bool(
        re.search(r"\b\d{4}\b|[’']\d{2}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2}\b", s)
    )

    if not user_has_year and dt.date() < local_now.date():
        dt = dt.replace(year=dt.year + 1)

    return dt.strftime(DATE_FMT)


def ensure_checkout(checkin_str: Optional[str], checkout_str: Optional[str], stay_days: Optional[int]):
    checkin = parse_date(checkin_str) if checkin_str else None
    checkout = parse_date(checkout_str) if checkout_str else None
    if checkin and checkout is None and stay_days:
        dt_checkin = datetime.strptime(checkin, DATE_FMT)
        dt_checkout = dt_checkin + timedelta(days=int(stay_days))
        checkout = dt_checkout.strftime(DATE_FMT)
    return checkin, checkout


def strip_code_fences(s: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", s.strip(), flags=re.IGNORECASE)


def parse_int_like(s: str) -> Optional[int]:
    s = (s or "").strip().lower()
    m = re.search(r"\d+", s)
    if m:
        return int(m.group(0))

    words = {
        "zero": 0, "none": 0, "no": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }
    return words.get(s)


def ask_json(llm: ChatOpenAI, system_prompt: str, user_prompt: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    res = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    raw = strip_code_fences(res.content)
    try:
        return json.loads(raw)
    except Exception:
        return fallback

def geocode_location(query: Optional[str]) -> Optional[Tuple[float, float]]:
    """
    Return (lat, lng) using Nominatim or None if not found.
    Why: downstream APIs often need coordinates; failure is non-fatal.
    """
    if not query or not str(query).strip():
        return None
    key = str(query).strip().lower()
    if key in _geocode_cache:
        return _geocode_cache[key]

    params = {
        "q": query,
        "format": "json",
        "addressdetails": 0,
        "limit": 1,
        "email": GEOCODER_NOMINATIM_EMAIL or "",
    }
    headers = {"User-Agent": GEOCODER_NOMINATIM_USER_AGENT}
    try:
        r = requests.get(GEOCODER_NOMINATIM_BASE_URL, params=params, headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json() or []
        if not data:
            return None
        lat, lon = data[0].get("lat"), data[0].get("lon")
        lat_f = float(lat) if lat is not None else None
        lon_f = float(lon) if lon is not None else None
        if lat_f is None or lon_f is None:
            return None
        if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0):
            return None
        _geocode_cache[key] = (lat_f, lon_f)
        return _geocode_cache[key]
    except Exception:
        return None
