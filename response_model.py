from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

class HotelItem(BaseModel):
    hotel_name: str = Field(..., description="Hotel display name")
    hotel_type: Optional[str] = Field(None, description="Vendor's category (e.g., '4 STARS')")
    price: Optional[float] = Field(None, ge=0, description="Minimum total price for the hotel")
    currency: Optional[str] = Field(None, description="Currency code for price (e.g., 'EUR')")
    latitude: Optional[float] = Field(None, description="Hotel latitude")
    longitude: Optional[float] = Field(None, description="Hotel longitude")

    @field_validator("currency")
    @classmethod
    def upper_currency(cls, v):
        return v.upper() if isinstance(v, str) else v


class HotelList(BaseModel):
    hotels: List[HotelItem]
