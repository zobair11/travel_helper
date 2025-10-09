from __future__ import annotations
from typing import Any, Dict, List, Optional
from response_model import HotelItem, HotelList

def _as_float(x: Any) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None

def _as_int(x: Any) -> Optional[int]:
    try:
        return int(float(x))
    except Exception:
        return None

def _get_hotel_array(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    hotels_root = payload.get("hotels")
    if isinstance(hotels_root, dict) and isinstance(hotels_root.get("hotels"), list):
        return [h for h in hotels_root["hotels"] if isinstance(h, dict)]
    return []

def _infer_min_price_and_currency(h: Dict[str, Any]) -> (Optional[float], Optional[str]):
    price = _as_float(h.get("minRate"))
    currency = h.get("currency")

    if price is not None and currency:
        return price, str(currency)

    best_price: Optional[float] = None
    best_currency: Optional[str] = str(currency) if currency else None

    rooms = h.get("rooms") or []
    for room in rooms:
        rates = room.get("rates") or []
        for r in rates:
            candidates = [
                _as_float(r.get("net")),
                _as_float(r.get("sellingRate")),
                _as_float(r.get("hotelSellingRate")),
            ]
            cand_price = min([c for c in candidates if c is not None], default=None)
            cand_currency = r.get("hotelCurrency") or h.get("currency")
            if cand_price is not None and (best_price is None or cand_price < best_price):
                best_price = cand_price
                best_currency = str(cand_currency) if cand_currency else best_currency

    return best_price, best_currency

def map_hotelbeds_payload(payload: Dict[str, Any]) -> HotelList:
    out: List[HotelItem] = []
    for h in _get_hotel_array(payload):
        price, currency = _infer_min_price_and_currency(h)

        item = HotelItem(
            hotel_name=str(h.get("name", "")),
            hotel_type=str(h.get("categoryName")) if h.get("categoryName") is not None else None,
            price=price,
            currency=str(currency) if currency else None,
            latitude=_as_float(h.get("latitude")),
            longitude=_as_float(h.get("longitude")),
        )
        out.append(item)

    return HotelList(hotels=out)