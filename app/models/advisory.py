from sqlalchemy import Column, String, Integer, Numeric, Date, Text, JSON
from app.database import Base

class PeerShowcaseField(Base):
    __tablename__ = "peer_showcase_fields"

    showcase_id = Column(String(50), primary_key=True, index=True)
    field_code = Column(String(20), nullable=False)
    district = Column(String(50), nullable=False)
    wheat_variety = Column(String(50), nullable=False)
    seed_company = Column(String(60), nullable=False)
    fertilizer_company = Column(String(60), nullable=False)
    area_acres = Column(Numeric(6, 2), nullable=False)
    shape_type = Column(String(15), nullable=False)  # square, rectangle, polygon, circle
    yield_maunds_per_acre = Column(Numeric(5, 1), nullable=False)
    yield_kg_sqm = Column(Numeric(5, 2), nullable=False)
    sowing_date = Column(Date, nullable=False)
    harvest_date = Column(Date, nullable=False)
    cycle_event_log = Column(JSON, nullable=False)

class AgronomicAdvisoryRule(Base):
    __tablename__ = "agronomic_advisory_rules"

    rule_id = Column(String(50), primary_key=True, index=True)
    stage_index = Column(Integer, nullable=False, index=True)  # 0 to 5
    stage_name = Column(String(30), nullable=False)
    summary_text_en = Column(Text, nullable=False)
    summary_text_ur = Column(Text, nullable=False)
    irrigation_advice_en = Column(Text, nullable=False)
    irrigation_advice_ur = Column(Text, nullable=False)
    nutrient_advice_en = Column(Text, nullable=False)
    nutrient_advice_ur = Column(Text, nullable=False)
    risk_alerts = Column(JSON, nullable=False)
    audio_script_ur = Column(Text, nullable=False)

