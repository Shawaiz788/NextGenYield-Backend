from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime

class FieldCreateRequest(BaseModel):
    field_name: str = Field(..., min_length=2, max_length=50, description="Display name for field parcel")
    shape_type: str = Field(..., description="square, rectangle, polygon, or circle")
    area_acres: float = Field(..., gt=0, description="Calculated area in acres")
    area_sqm: Optional[float] = Field(None, description="Calculated area in square meters")
    boundary_geojson: Dict[str, Any] = Field(..., description="RFC 7946 GeoJSON boundary polygon")
    center_latitude: Optional[float] = Field(None, description="Centroid latitude")
    center_longitude: Optional[float] = Field(None, description="Centroid longitude")

    @field_validator("shape_type")
    @classmethod
    def validate_shape(cls, v: str) -> str:
        if v.lower() not in ("square", "rectangle", "polygon", "circle"):
            raise ValueError("shape_type must be square, rectangle, polygon, or circle")
        return v.lower()

class FieldUpdateRequest(BaseModel):
    field_name: Optional[str] = Field(None, min_length=2, max_length=50)

class FieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field_id: str
    user_id: str
    field_name: str
    shape_type: str
    area_acres: float
    area_sqm: float
    boundary_geojson: Dict[str, Any]
    center_latitude: float
    center_longitude: float
    current_cycle_id: Optional[str] = None
    created_at: datetime
