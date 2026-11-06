from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import List
import uuid
from app.database import get_db
from app.models.user import User
from app.models.field import Field
from app.models.crop_cycle import CropCycle
from app.models.schedule import FertilizerSchedule, IrrigationSchedule
from app.schemas.crop_cycle import (
    StartCropCycleRequest,
    CropCycleResponse,
    FertilizerScheduleResponse,
    IrrigationScheduleResponse,
)
from app.services.agronomic_engine import generate_default_schedules
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/crop-cycles", tags=["Crop Cycles & Management"])

@router.post("/start", response_model=CropCycleResponse, status_code=status.HTTP_201_CREATED)
def start_crop_cycle(
    req: StartCropCycleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Use Case 4: Starting a Crop Cycle (Table 4.4 in F26-201).
    Activates an unstarted field by recording seed variety, seed provider, fertilizer brand,
    sowing technique, and sowing date, automatically generating the 140-day crop schedules.
    """
    field = db.query(Field).filter(
        Field.field_id == req.field_id,
        Field.user_id == current_user.user_id
    ).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    cycle_id = f"cyc_{uuid.uuid4().hex[:12]}"
    target_harvest = req.target_harvest_date or (req.sowing_date + timedelta(days=140))

    new_cycle = CropCycle(
        cycle_id=cycle_id,
        field_id=field.field_id,
        wheat_variety=req.wheat_variety,
        seed_company=req.seed_company,
        fertilizer_company=req.fertilizer_company,
        sowing_method=req.sowing_method,
        sowing_date=req.sowing_date,
        target_harvest_date=target_harvest,
        is_active=True,
    )
    db.add(new_cycle)

    field.current_cycle_id = cycle_id

    fert_list, irrig_list = generate_default_schedules(cycle_id, req.sowing_date)
    for fert in fert_list:
        db.add(fert)
    for irrig in irrig_list:
        db.add(irrig)

    db.commit()
    db.refresh(new_cycle)

    return CropCycleResponse(
        cycle_id=new_cycle.cycle_id,
        field_id=new_cycle.field_id,
        wheat_variety=new_cycle.wheat_variety,
        seed_company=new_cycle.seed_company,
        fertilizer_company=new_cycle.fertilizer_company,
        sowing_method=new_cycle.sowing_method,
        sowing_date=new_cycle.sowing_date,
        target_harvest_date=new_cycle.target_harvest_date,
        is_active=new_cycle.is_active,
        created_at=new_cycle.created_at,
        fertilizer_schedules=[FertilizerScheduleResponse.model_validate(f) for f in fert_list],
        irrigation_schedules=[IrrigationScheduleResponse.model_validate(i) for i in irrig_list],
    )

@router.get("/{cycle_id}", response_model=CropCycleResponse)
def get_cycle_details(
    cycle_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve active cycle along with its fertilizer and irrigation schedules."""
    cycle = db.query(CropCycle).filter(CropCycle.cycle_id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop cycle not found")

    field = db.query(Field).filter(
        Field.field_id == cycle.field_id,
        Field.user_id == current_user.user_id
    ).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    ferts = db.query(FertilizerSchedule).filter(FertilizerSchedule.cycle_id == cycle_id).order_by(FertilizerSchedule.split_number).all()
    irrigs = db.query(IrrigationSchedule).filter(IrrigationSchedule.cycle_id == cycle_id).order_by(IrrigationSchedule.target_das).all()

    return CropCycleResponse(
        cycle_id=cycle.cycle_id,
        field_id=cycle.field_id,
        wheat_variety=cycle.wheat_variety,
        seed_company=cycle.seed_company,
        fertilizer_company=cycle.fertilizer_company,
        sowing_method=cycle.sowing_method,
        sowing_date=cycle.sowing_date,
        target_harvest_date=cycle.target_harvest_date,
        is_active=cycle.is_active,
        created_at=cycle.created_at,
        fertilizer_schedules=[FertilizerScheduleResponse.model_validate(f) for f in ferts],
        irrigation_schedules=[IrrigationScheduleResponse.model_validate(i) for i in irrigs],
    )

@router.put("/fertilizer/{fertilizer_id}/apply", response_model=FertilizerScheduleResponse)
def mark_fertilizer_applied(
    fertilizer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Farmer confirms fertilizer split has been applied to the field."""
    item = db.query(FertilizerSchedule).filter(FertilizerSchedule.fertilizer_id == fertilizer_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fertilizer record not found")

    item.is_applied = True
    item.applied_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return item

@router.put("/irrigation/{irrigation_id}/complete", response_model=IrrigationScheduleResponse)
def mark_irrigation_completed(
    irrigation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Farmer marks irrigation milestone event completed."""
    item = db.query(IrrigationSchedule).filter(IrrigationSchedule.irrigation_id == irrigation_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Irrigation record not found")

    item.is_completed = True
    db.commit()
    db.refresh(item)
    return item
