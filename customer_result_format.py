from __future__ import annotations
from typing import Iterable
from response_model import HotelItem

def format_customer_list(items: Iterable[HotelItem]) -> str:
    lines = []
    for idx, h in enumerate(items, start=1):
        price = h.price
        currency = h.currency
        price_str = "N/A"
        if price is not None:
            price_str = f"{int(price):,} {currency}" if float(price).is_integer() else f"{price:,.2f} {currency}"

        star_str = h.hotel_type

        lines.append(f"{idx}. Hotel name: {h.hotel_name}")
        lines.append(f"   Hotel type: {star_str}")
        lines.append(f"   latitude: {h.latitude}")
        lines.append(f"   longitude: {h.longitude}")
        lines.append(f"   Total Price: {price_str}")
        lines.append("") 
    return "\n".join(lines).rstrip()