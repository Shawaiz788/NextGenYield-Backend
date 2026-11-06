from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app.models.user import User
from app.models.crop_cycle import CropCycle
from app.models.observation import FieldObservation
from app.schemas.observation import ObservationResponse
from app.services.supabase_storage import SupabaseStorageService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/observations", tags=["Field Observations & Timeline"])

@router.post("/", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED)
async def create_field_observation(
    cycle_id: str = Form(...),
    stage_index: int = Form(...),
    stage_name: str = Form(...),
    confidence: float = Form(...),
    pitch_angle_deg: float = Form(...),
    blur_score: float = Form(...),
    das: int = Form(...),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Use Case 5 & 7: Crop Canopy Scanning and Timeline Logging (Table 4.5 & 4.7 in F26-201).
    Uploads canopy image to Supabase Storage and records observation record.
    """
    # Verify crop cycle exists
    cycle = db.query(CropCycle).filter(CropCycle.cycle_id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop cycle not found")

    # Read image contents & upload to Supabase Storage
    image_bytes = await image.read()
    image_uri = SupabaseStorageService.upload_image(
        file_bytes=image_bytes,
        file_name=image.filename or "observation.jpg",
        content_type=image.content_type or "image/jpeg"
    )

    observation_id = f"obs_{uuid.uuid4().hex[:12]}"
    new_obs = FieldObservation(
        observation_id=observation_id,
        cycle_id=cycle_id,
        image_uri=image_uri,
        stage_index=stage_index,
        stage_name=stage_name,
        confidence=confidence,
        pitch_angle_deg=pitch_angle_deg,
        blur_score=blur_score,
        das=das,
    )
    db.add(new_obs)
    db.commit()
    db.refresh(new_obs)
    return new_obs

@router.get("/cycle/{cycle_id}", response_model=List[ObservationResponse])
def get_cycle_timeline(
    cycle_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Use Case 7: Timeline Tracking (Table 4.7 in F26-201).
    Retrieves chronological ledger of all visual observations logged since sowing.
    """
    observations = db.query(FieldObservation).filter(
        FieldObservation.cycle_id == cycle_id
    ).order_by(FieldObservation.captured_at.asc()).all()
    return observations

