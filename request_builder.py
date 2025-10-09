from __future__ import annotations
import json
from typing import Dict, Any
from state import TravelState

def build_search_request(state: TravelState, radius_km: int = 20) -> Dict[str, Any]:
    missing = []
    for key in ("checkin", "checkout", "adults", "rooms"):
        if not state.get(key) and state.get(key) != 0:
            missing.append(key)
    if state.get("children") is None:
        missing.append("children")
    if state.get("lat") is None or state.get("lng") is None:
        missing.append("lat/lng")
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    adults = int(state["adults"])
    children = int(state.get("children", 0))
    rooms = int(state["rooms"])

    body: Dict[str, Any] = {
        "stay": {
            "checkIn": str(state["checkin"]),
            "checkOut": str(state["checkout"]),
        },
        "occupancies": [
            {
                "rooms": rooms,
                "adults": adults,
                "children": children,
            }
        ],
        "geolocation": {
            "latitude": float(state["lat"]),
            "longitude": float(state["lng"]),
            "radius": int(radius_km),
            "unit": "km",
        },
    }
    return body

def to_pretty_json(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)



