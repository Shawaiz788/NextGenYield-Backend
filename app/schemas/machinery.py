from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class MachineryListingCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., max_length=100)
    machinery_type: str = Field(..., max_length=40)  # tractor, laser_leveler, rotavator, seed_drill, chisel_plow, combine_harvester, disc_harrow
    brand_model: Optional[str] = Field(None, max_length=80)
    horsepower: Optional[float] = None
    hourly_rate_pkr: Optional[float] = None
    daily_rate_pkr: float = Field(..., gt=0)
    district: str = Field(..., max_length=50)
    location_address: Optional[str] = Field(None, max_length=200)
    contact_phone: str = Field(..., max_length=20)
    description: Optional[str] = None
    image_url: Optional[str] = None

class MachineryBookingCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start_date: datetime
    end_date: datetime
    total_hours: Optional[float] = None
    purpose_step: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None

class MachineryBookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    booking_id: str
    machinery_id: str
    renter_id: str
    start_date: datetime
    end_date: datetime
    total_hours: Optional[float] = None
    total_amount_pkr: float
    status: str
    purpose_step: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

class MachineryListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    machinery_id: str
    owner_id: str
    title: str
    machinery_type: str
    brand_model: Optional[str] = None
    horsepower: Optional[float] = None
    hourly_rate_pkr: Optional[float] = None
    daily_rate_pkr: float
    district: str
    location_address: Optional[str] = None
    contact_phone: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool
    created_at: datetime
    bookings: Optional[List[MachineryBookingResponse]] = None
