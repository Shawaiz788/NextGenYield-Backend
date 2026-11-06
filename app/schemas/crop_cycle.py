from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime

class StartCropCycleRequest(BaseModel):
    field_id: str = Field(..., description="Field identifier to associate cycle with")
    wheat_variety: str = Field(..., min_length=2, max_length=50, description="Cultivar name e.g. Akbar-19, Dilkash-20")
    seed_company: str = Field(..., min_length=2, max_length=60, description="Certified seed provider or agency")
    fertilizer_company: str = Field(..., min_length=2, max_length=60, description="FFC, Engro, Fatima, etc.")
    sowing_method: str = Field("Drill Sowing", max_length=30, description="Drill, Broadcast, or Bed Planting")
    sowing_date: date = Field(..., description="Date of sowing into moist soil")
    target_harvest_date: Optional[date] = Field(None, description="Projected maturity harvest date (approx 140 days)")

class FertilizerScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fertilizer_id: str
    cycle_id: str
    split_number: int
    nutrient_type: str
    target_das: int
    dose_per_acre: str
    is_applied: bool
    applied_at: Optional[datetime] = None

class IrrigationScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    irrigation_id: str
    cycle_id: str
    event_name: str
    water_source: str
    target_das: int
    is_completed: bool

class CropCycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cycle_id: str
    field_id: str
    wheat_variety: str
    seed_company: str
    fertilizer_company: str
    sowing_method: str
    sowing_date: date
    target_harvest_date: date
    is_active: bool
    created_at: datetime
    fertilizer_schedules: Optional[List[FertilizerScheduleResponse]] = []
    irrigation_schedules: Optional[List[IrrigationScheduleResponse]] = []
