from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class MarketplaceItemCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., max_length=100)
    category: str = Field(..., max_length=40)  # seeds, fertilizer, machinery, wheat_grain, pesticides, land_lease, other
    price_pkr: float = Field(..., gt=0)
    condition: str = Field("new", max_length=20)  # new, used, refurbished
    district: str = Field(..., max_length=50)
    location_address: Optional[str] = Field(None, max_length=200)
    contact_phone: str = Field(..., max_length=20)
    description: str
    image_url: Optional[str] = None

class MarketplaceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: str
    seller_id: str
    seller_name: str
    seller_phone: str
    title: str
    category: str
    price_pkr: float
    condition: str
    district: str
    location_address: Optional[str] = None
    description: str
    image_url: Optional[str] = None
    is_sold: bool
    created_at: datetime
