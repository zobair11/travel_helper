from __future__ import annotations
import os
import json
from typing import Any, Dict, Optional
import requests
from api_signing import make_signature

TIMEOUT_SECONDS = 5 

class ApiError(RuntimeError):
    pass

def _headers() -> Dict[str, str]:
    api_key = os.getenv("API_KEY")
    secret = os.getenv("API_SIGNATURE_SECRET")
    if not api_key:
        raise ApiError("API_KEY is not set")
    if not secret:
        raise ApiError("API_SIGNATURE_SECRET is not set")

    sig, ts = make_signature(api_key, secret)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Api-key": api_key,
        "X-Signature": sig,
    }

    if os.getenv("SIGN_INCLUDE_TS") == "1":
        headers["X-Timestamp"] = str(ts)
    return headers

def post_availability(payload: Dict[str, Any], *, path: str = "/hotel-api/1.0/hotels", base_url: Optional[str] = None) -> Dict[str, Any]:
    base = base_url or os.getenv("API_BASE_URL")
    if not base:
        raise ApiError("API_BASE_URL is not set")
    url = base.rstrip("/") + path
    try:
        resp = requests.post(url, data=json.dumps(payload), headers=_headers(), timeout=TIMEOUT_SECONDS)
    except requests.RequestException as e:
        raise ApiError(f"HTTP error: {e}") from e

    if resp.status_code >= 400:
        snippet = resp.text[:500]
        raise ApiError(f"{resp.status_code} {resp.reason}: {snippet}")

    try:
        return resp.json()
    except ValueError:
        raise ApiError("Response is not valid JSON")


def preview(obj: Any, max_len: int = 2000) -> str:
    try:
        s = json.dumps(obj, indent=2, ensure_ascii=False)
        return s if len(s) <= max_len else s[:max_len] + "\n... (truncated)"
    except Exception:
        return str(obj)