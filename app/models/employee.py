from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from datetime import datetime
from app.database import Base

class FarmEmployee(Base):
    __tablename__ = "farm_employees"

    employee_record_id = Column(String(50), primary_key=True, index=True)
    owner_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    employee_user_id = Column(String(50), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    employee_name = Column(String(60), nullable=False)
    employee_phone = Column(String(20), nullable=False, index=True)
    role = Column(String(30), nullable=False, default="farmhand")  # farmhand, operator, agronomist, manager
    status = Column(String(20), nullable=False, default="active")  # active, invited, suspended
    access_all_fields = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class FieldAssignment(Base):
    __tablename__ = "field_assignments"

    assignment_id = Column(String(50), primary_key=True, index=True)
    employee_record_id = Column(String(50), ForeignKey("farm_employees.employee_record_id", ondelete="CASCADE"), nullable=False, index=True)
    field_id = Column(String(50), ForeignKey("fields.field_id", ondelete="CASCADE"), nullable=False, index=True)
    can_scan = Column(Boolean, nullable=False, default=True)
    can_edit_schedule = Column(Boolean, nullable=False, default=False)
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
