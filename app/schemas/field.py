from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime, date

MAX_FIELD_ACRES = 5000.0
MAX_FIELD_SQM = 25_000_000.0

# Attach soil_texture property to ORM Field model dynamically so from_attributes can resolve it
try:
    from app.models.field import Field as ORMField
    if not hasattr(ORMField, "soil_texture"):
        ORMField.soil_texture = property(
            lambda self: (self.boundary_geojson or {}).get("properties", {}).get("soil_texture")
            if isinstance(self.boundary_geojson, dict)
            else None
        )
except Exception:
    pass

class FieldCreateRequest(BaseModel):
    field_name: str = Field(..., min_length=2, max_length=50, description="Display name for field parcel")
    shape_type: str = Field(..., description="square, rectangle, polygon, or circle")
    area_acres: float = Field(..., gt=0, description="Calculated area in acres")
    area_sqm: Optional[float] = Field(None, gt=0, description="Calculated area in square meters")
    boundary_geojson: Dict[str, Any] = Field(..., description="RFC 7946 GeoJSON boundary polygon")
    center_latitude: Optional[float] = Field(None, description="Centroid latitude")
    center_longitude: Optional[float] = Field(None, description="Centroid longitude")

    @field_validator("area_acres")
    @classmethod
    def validate_area_acres(cls, v: float) -> float:
        if v > MAX_FIELD_ACRES:
            raise ValueError(
                f"Field area ({v:,.2f} acres) exceeds the maximum allowed limit of {MAX_FIELD_ACRES:,.0f} acres. Please demarcate a smaller farm parcel."
            )
        return round(v, 2)

    @field_validator("area_sqm")
    @classmethod
    def validate_area_sqm(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v > MAX_FIELD_SQM:
            raise ValueError(
                f"Field area in square meters exceeds the maximum allowed limit ({MAX_FIELD_ACRES:,.0f} acres)."
            )
        return round(v, 2) if v is not None else None

    @field_validator("shape_type")
    @classmethod
    def validate_shape(cls, v: str) -> str:
        if v.lower() not in ("square", "rectangle", "polygon", "circle"):
            raise ValueError("shape_type must be square, rectangle, polygon, or circle")
        return v.lower()

class FieldUpdateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field_name: Optional[str] = Field(None, min_length=2, max_length=50, description="Updated display name")
    shape_type: Optional[str] = Field(None, description="square, rectangle, polygon, or circle")
    area_acres: Optional[float] = Field(None, gt=0, description="Updated area in acres")
    area_sqm: Optional[float] = Field(None, gt=0, description="Updated area in square meters")
    boundary_geojson: Optional[Dict[str, Any]] = Field(None, description="RFC 7946 GeoJSON boundary polygon")
    coordinates: Optional[List[Any]] = Field(None, description="Raw coordinates list e.g. [[lng, lat], ...]")
    center_latitude: Optional[float] = Field(None, description="Centroid latitude")
    center_longitude: Optional[float] = Field(None, description="Centroid longitude")
    soil_texture: Optional[str] = Field(None, description="Agronomic soil classification e.g. Clay Loam, Sandy Loam")

    @field_validator("area_acres")
    @classmethod
    def validate_update_area_acres(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v > MAX_FIELD_ACRES:
            raise ValueError(
                f"Field area ({v:,.2f} acres) exceeds the maximum allowed limit of {MAX_FIELD_ACRES:,.0f} acres."
            )
        return round(v, 2) if v is not None else None

    @field_validator("area_sqm")
    @classmethod
    def validate_update_area_sqm(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v > MAX_FIELD_SQM:
            raise ValueError(
                f"Field area in square meters exceeds the maximum allowed limit ({MAX_FIELD_ACRES:,.0f} acres)."
            )
        return round(v, 2) if v is not None else None

    @field_validator("shape_type")
    @classmethod
    def validate_shape(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.lower() not in ("square", "rectangle", "polygon", "circle"):
            raise ValueError("shape_type must be square, rectangle, polygon, or circle")
        return v.lower() if v is not None else None

class FieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field_id: str
    field_code: Optional[str] = None
    user_id: str
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    owner_district: Optional[str] = None
    is_mine: bool = True
    field_name: str
    shape_type: str
    area_acres: float
    area_sqm: float
    boundary_geojson: Dict[str, Any]
    center_latitude: float
    center_longitude: float
    current_cycle_id: Optional[str] = None
    wheat_variety: Optional[str] = None
    seed_company: Optional[str] = None
    fertilizer_company: Optional[str] = None
    sowing_date: Optional[date] = None
    target_harvest_date: Optional[date] = None
    cycle_status: str = "not_started"
    current_stage_index: int = 0
    days_after_sowing: Optional[int] = None
    soil_texture: Optional[str] = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def populate_soil_texture(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "soil_texture" not in data or data.get("soil_texture") is None:
                bg = data.get("boundary_geojson", {})
                if isinstance(bg, dict):
                    data["soil_texture"] = bg.get("properties", {}).get("soil_texture")
        return data
