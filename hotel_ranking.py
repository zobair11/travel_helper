from __future__ import annotations
from typing import List
from response_model import HotelItem

def sort_hotels_by_price(hotels: List[HotelItem]) -> List[HotelItem]:
    return sorted(hotels, key=lambda h: (h.price is None, h.price if h.price is not None else float("inf")))

def top_n_cheapest(hotels: List[HotelItem], n: int = 10) -> List[HotelItem]:
    return sort_hotels_by_price(hotels)[:max(0, int(n))]
