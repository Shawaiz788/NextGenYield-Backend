from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class EmployeeCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_name: str = Field(..., max_length=60)
    employee_phone: str = Field(..., max_length=20)
    role: str = Field("farmhand", max_length=30)  # farmhand, operator, agronomist, manager
    access_all_fields: bool = False
    assigned_field_ids: Optional[List[str]] = []

class AssignFieldsRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field_ids: List[str]
    access_all_fields: bool = False

class FieldAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assignment_id: str
    employee_record_id: str
    field_id: str
    field_name: Optional[str] = None
    can_scan: bool
    can_edit_schedule: bool
    assigned_at: datetime

class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_record_id: str
    owner_id: str
    employee_user_id: Optional[str] = None
    employee_name: str
    employee_phone: str
    role: str
    status: str
    access_all_fields: bool
    created_at: datetime
    assigned_fields: Optional[List[FieldAssignmentResponse]] = []
