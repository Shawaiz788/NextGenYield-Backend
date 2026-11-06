from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class FieldObservation(Base):
    __tablename__ = "field_observations"

    observation_id = Column(String(50), primary_key=True, index=True)
    cycle_id = Column(String(50), ForeignKey("crop_cycles.cycle_id", ondelete="CASCADE"), nullable=False, index=True)
    image_uri = Column(String(255), nullable=False)
    stage_index = Column(Integer, nullable=False)
    stage_name = Column(String(30), nullable=False)
    confidence = Column(Numeric(5, 2), nullable=False)
    pitch_angle_deg = Column(Numeric(4, 1), nullable=False)
    blur_score = Column(Numeric(6, 2), nullable=False)
    das = Column(Integer, nullable=False)  # Days After Sowing
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow)

