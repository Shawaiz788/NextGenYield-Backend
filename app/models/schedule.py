from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from app.database import Base

class FertilizerSchedule(Base):
    __tablename__ = "fertilizer_schedules"

    fertilizer_id = Column(String(50), primary_key=True, index=True)
    cycle_id = Column(String(50), ForeignKey("crop_cycles.cycle_id", ondelete="CASCADE"), nullable=False, index=True)
    split_number = Column(Integer, nullable=False)  # 1 to 3
    nutrient_type = Column(String(40), nullable=False)
    target_das = Column(Integer, nullable=False)
    dose_per_acre = Column(String(50), nullable=False)
    is_applied = Column(Boolean, nullable=False, default=False)
    applied_at = Column(DateTime, nullable=True)

class IrrigationSchedule(Base):
    __tablename__ = "irrigation_schedules"

    irrigation_id = Column(String(50), primary_key=True, index=True)
    cycle_id = Column(String(50), ForeignKey("crop_cycles.cycle_id", ondelete="CASCADE"), nullable=False, index=True)
    event_name = Column(String(40), nullable=False)
    water_source = Column(String(30), nullable=False)
    target_das = Column(Integer, nullable=False)
    is_completed = Column(Boolean, nullable=False, default=False)

