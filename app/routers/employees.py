from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database import get_db
from app.models.user import User
from app.models.field import Field
from app.models.employee import FarmEmployee, FieldAssignment
from app.schemas.employee import (
    EmployeeCreateRequest,
    EmployeeResponse,
    AssignFieldsRequest,
    FieldAssignmentResponse,
)
from app.schemas.field import FieldResponse
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/employees", tags=["Farm Team & Delegation"])

@router.get("/", response_model=List[EmployeeResponse])
def list_employees(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all employees/operators registered by the farm owner."""
    employees = db.query(FarmEmployee).filter(FarmEmployee.owner_id == current_user.user_id).all()
    result = []
    for emp in employees:
        assignments = db.query(FieldAssignment).filter(FieldAssignment.employee_record_id == emp.employee_record_id).all()
        field_assignments = []
        for a in assignments:
            field = db.query(Field).filter(Field.field_id == a.field_id).first()
            field_assignments.append(FieldAssignmentResponse(
                assignment_id=a.assignment_id,
                employee_record_id=a.employee_record_id,
                field_id=a.field_id,
                field_name=field.field_name if field else "Field",
                can_scan=a.can_scan,
                can_edit_schedule=a.can_edit_schedule,
                assigned_at=a.assigned_at
            ))
        result.append(EmployeeResponse(
            employee_record_id=emp.employee_record_id,
            owner_id=emp.owner_id,
            employee_user_id=emp.employee_user_id,
            employee_name=emp.employee_name,
            employee_phone=emp.employee_phone,
            role=emp.role,
            status=emp.status,
            access_all_fields=emp.access_all_fields,
            created_at=emp.created_at,
            assigned_fields=field_assignments
        ))
    return result

@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def add_employee(
    req: EmployeeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new farm employee and optionally assign initial fields."""
    # Check if employee user account exists by phone number
    existing_user = db.query(User).filter(User.phone_number == req.employee_phone).first()

    emp_id = f"emp_{uuid.uuid4().hex[:8]}"
    employee = FarmEmployee(
        employee_record_id=emp_id,
        owner_id=current_user.user_id,
        employee_user_id=existing_user.user_id if existing_user else None,
        employee_name=req.employee_name,
        employee_phone=req.employee_phone,
        role=req.role,
        status="active",
        access_all_fields=req.access_all_fields,
    )
    db.add(employee)
    db.flush()

    assignments = []
    if req.assigned_field_ids and not req.access_all_fields:
        for f_id in req.assigned_field_ids:
            # Verify field belongs to owner
            field = db.query(Field).filter(Field.field_id == f_id, Field.user_id == current_user.user_id).first()
            if field:
                assign_id = f"asgn_{uuid.uuid4().hex[:8]}"
                assignment = FieldAssignment(
                    assignment_id=assign_id,
                    employee_record_id=emp_id,
                    field_id=f_id,
                    can_scan=True,
                    can_edit_schedule=False,
                )
                db.add(assignment)
                assignments.append(FieldAssignmentResponse(
                    assignment_id=assign_id,
                    employee_record_id=emp_id,
                    field_id=f_id,
                    field_name=field.field_name,
                    can_scan=True,
                    can_edit_schedule=False,
                    assigned_at=assignment.assigned_at or employee.created_at
                ))

    db.commit()
    db.refresh(employee)

    return EmployeeResponse(
        employee_record_id=employee.employee_record_id,
        owner_id=employee.owner_id,
        employee_user_id=employee.employee_user_id,
        employee_name=employee.employee_name,
        employee_phone=employee.employee_phone,
        role=employee.role,
        status=employee.status,
        access_all_fields=employee.access_all_fields,
        created_at=employee.created_at,
        assigned_fields=assignments
    )

@router.post("/{employee_record_id}/assign-fields", response_model=EmployeeResponse)
def assign_fields_to_employee(
    employee_record_id: str,
    req: AssignFieldsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update assigned fields for an existing employee."""
    employee = db.query(FarmEmployee).filter(
        FarmEmployee.employee_record_id == employee_record_id,
        FarmEmployee.owner_id == current_user.user_id
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found.")

    employee.access_all_fields = req.access_all_fields
    # Remove previous assignments
    db.query(FieldAssignment).filter(FieldAssignment.employee_record_id == employee_record_id).delete()

    assignments = []
    if not req.access_all_fields:
        for f_id in req.field_ids:
            field = db.query(Field).filter(Field.field_id == f_id, Field.user_id == current_user.user_id).first()
            if field:
                assign_id = f"asgn_{uuid.uuid4().hex[:8]}"
                assignment = FieldAssignment(
                    assignment_id=assign_id,
                    employee_record_id=employee_record_id,
                    field_id=f_id,
                    can_scan=True,
                    can_edit_schedule=False,
                )
                db.add(assignment)
                assignments.append(FieldAssignmentResponse(
                    assignment_id=assign_id,
                    employee_record_id=employee_record_id,
                    field_id=f_id,
                    field_name=field.field_name,
                    can_scan=True,
                    can_edit_schedule=False,
                    assigned_at=assignment.assigned_at
                ))
    
    db.commit()
    db.refresh(employee)

    return EmployeeResponse(
        employee_record_id=employee.employee_record_id,
        owner_id=employee.owner_id,
        employee_user_id=employee.employee_user_id,
        employee_name=employee.employee_name,
        employee_phone=employee.employee_phone,
        role=employee.role,
        status=employee.status,
        access_all_fields=employee.access_all_fields,
        created_at=employee.created_at,
        assigned_fields=assignments
    )

@router.delete("/{employee_record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove employee from farm team and revoke all access."""
    employee = db.query(FarmEmployee).filter(
        FarmEmployee.employee_record_id == employee_record_id,
        FarmEmployee.owner_id == current_user.user_id
    ).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    
    db.query(FieldAssignment).filter(FieldAssignment.employee_record_id == employee_record_id).delete()
    db.delete(employee)
    db.commit()
    return None

@router.get("/assigned-to-me", response_model=List[FieldResponse])
def get_fields_assigned_to_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all fields delegated to the currently logged in employee/farmhand."""
    # Find employee records matching user id or phone
    emp_records = db.query(FarmEmployee).filter(
        (FarmEmployee.employee_user_id == current_user.user_id) |
        (FarmEmployee.employee_phone == current_user.phone_number)
    ).all()

    if not emp_records:
        return []

    assigned_fields = []
    seen_field_ids = set()

    for emp in emp_records:
        if emp.access_all_fields:
            # Grant access to all owner fields
            owner_fields = db.query(Field).filter(Field.user_id == emp.owner_id).all()
            for f in owner_fields:
                if f.field_id not in seen_field_ids:
                    seen_field_ids.add(f.field_id)
                    assigned_fields.append(f)
        else:
            assignments = db.query(FieldAssignment).filter(FieldAssignment.employee_record_id == emp.employee_record_id).all()
            for a in assignments:
                if a.field_id not in seen_field_ids:
                    f = db.query(Field).filter(Field.field_id == a.field_id).first()
                    if f:
                        seen_field_ids.add(f.field_id)
                        assigned_fields.append(f)

    return assigned_fields
