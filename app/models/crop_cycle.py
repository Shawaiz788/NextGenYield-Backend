from sqlalchemy import Column, String, Date, Boolean, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class CropCycle(Base):
    __tablename__ = "crop_cycles"

    cycle_id = Column(String(50), primary_key=True, index=True)
    field_id = Column(String(50), ForeignKey("fields.field_id", ondelete="CASCADE"), nullable=False, index=True)
    wheat_variety = Column(String(50), nullable=False)
    seed_company = Column(String(60), nullable=False)
    fertilizer_company = Column(String(60), nullable=False)
    sowing_method = Column(String(30), nullable=False)
    sowing_date = Column(Date, nullable=False)
    target_harvest_date = Column(Date, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

