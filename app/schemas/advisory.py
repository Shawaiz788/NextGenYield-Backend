"""
backend/app/schemas/advisory.py
Pydantic v2 schemas for deterministic advisory rules and peer farmer showcase benchmarks.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import date

class ShowcaseCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = Field(None, min_length=2, max_length=100, description="Title of the showcase plot")
    field_name: Optional[str] = Field(None, max_length=50, description="Farmer field name or plot identifier")
    field_code: Optional[str] = Field(None, max_length=50, description="Unique field code e.g. PK-FSD-01")
    region: Optional[str] = Field(None, max_length=50, description="District or agricultural zone e.g. Faisalabad")
    district: Optional[str] = Field(None, max_length=50, description="District name")
    wheat_variety: str = Field(..., min_length=2, max_length=50, description="Wheat cultivar name e.g. Akbar-2019, Dilkash-20")
    actual_yield_maunds: Optional[float] = Field(None, gt=0, description="Actual recorded yield in Maunds per Acre")
    yield_maunds_per_acre: Optional[float] = Field(None, gt=0, description="Actual recorded yield in Maunds per Acre")
    yield_kg_sqm: Optional[float] = Field(None, gt=0, description="Calculated yield in kg/m²")
    sowing_date: date = Field(..., description="Date of sowing (YYYY-MM-DD)")
    harvesting_date: Optional[date] = Field(None, description="Date of harvest (YYYY-MM-DD)")
    harvest_date: Optional[date] = Field(None, description="Date of harvest (YYYY-MM-DD)")
    key_tactics: Optional[Union[str, List[str], List[Dict[str, Any]]]] = Field(
        None, description="Key agronomic practices or event playbook"
    )
    cycle_event_log: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, description="Chronological event log"
    )
    photo_url: Optional[str] = Field(None, description="URL of field canopy photo or harvest verification")
    seed_company: Optional[str] = Field("Punjab Seed Corporation (PSC)", max_length=60, description="Seed company or provider")
    fertilizer_company: Optional[str] = Field("Fauji Fertilizer Company (FFC)", max_length=60, description="Fertilizer provider")
    area_acres: Optional[float] = Field(1.0, gt=0, description="Plot area in acres")
    shape_type: Optional[str] = Field("rectangle", description="Field shape type (square, rectangle, polygon, circle)")

class PeerShowcaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    showcase_id: str
    field_code: str
    district: str
    wheat_variety: str
    seed_company: str
    fertilizer_company: str
    area_acres: float
    shape_type: str
    yield_maunds_per_acre: float
    yield_kg_sqm: float
    sowing_date: date
    harvest_date: date
    cycle_event_log: List[Dict[str, Any]]

class AdvisoryRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    stage_index: int
    stage_name: str
    summary_text_en: str
    summary_text_ur: str
    irrigation_advice_en: str
    irrigation_advice_ur: str
    nutrient_advice_en: str
    nutrient_advice_ur: str
    risk_alerts: List[Dict[str, Any]]
    audio_script_ur: str
