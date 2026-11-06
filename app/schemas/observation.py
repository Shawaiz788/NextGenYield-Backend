from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class ObservationCreateRequest(BaseModel):
    cycle_id: str
    image_uri: str
    stage_index: int = Field(..., ge=0, le=5)
    stage_name: str
    confidence: float
    pitch_angle_deg: float
    blur_score: float
    das: int

class ObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    observation_id: str
    cycle_id: str
    image_uri: str
    stage_index: int
    stage_name: str
    confidence: float
    pitch_angle_deg: float
    blur_score: float
    das: int
    captured_at: datetime

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
