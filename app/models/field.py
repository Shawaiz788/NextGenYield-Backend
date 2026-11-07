from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, JSON
from datetime import datetime
from app.database import Base

class Field(Base):
    __tablename__ = "fields"

    field_id = Column(String(50), primary_key=True, index=True)
    field_code = Column(String(20), nullable=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(50), nullable=False)
    shape_type = Column(String(15), nullable=False)  # square, rectangle, polygon, circle
    area_acres = Column(Numeric(6, 2), nullable=False)
    area_sqm = Column(Numeric(10, 2), nullable=False)
    boundary_geojson = Column(JSON, nullable=False)
    center_latitude = Column(Numeric(9, 6), nullable=False)
    center_longitude = Column(Numeric(9, 6), nullable=False)
    current_cycle_id = Column(String(50), ForeignKey("crop_cycles.cycle_id", ondelete="SET NULL", use_alter=True, name="fk_fields_current_cycle"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

