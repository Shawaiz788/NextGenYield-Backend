from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.database import get_db
from app.models.user import User
from app.models.field import Field
from app.models.crop_cycle import CropCycle
from app.schemas.field import (
    FieldCreateRequest,
    FieldUpdateRequest,
    FieldResponse,
)
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/fields", tags=["Fields & Demarcation"])

def calculate_centroid(geojson: dict) -> tuple[float, float]:
    """Calculate approximate center latitude & longitude from GeoJSON geometry."""
    try:
        coords = []
        if geojson.get("type") == "Polygon" and geojson.get("coordinates"):
            coords = geojson["coordinates"][0]
        elif geojson.get("type") == "Feature" and geojson.get("geometry", {}).get("coordinates"):
            coords = geojson["geometry"]["coordinates"][0]
        
        if coords:
            # coords are [lng, lat]
            avg_lng = sum(p[0] for p in coords) / len(coords)
            avg_lat = sum(p[1] for p in coords) / len(coords)
            return round(avg_lat, 6), round(avg_lng, 6)
    except Exception:
        pass
    # Fallback default (Faisalabad / Lahore Indus Basin coords)
    return 31.418715, 73.079109

@router.get("/", response_model=List[FieldResponse])
def get_user_fields(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all demarcated farm parcels belonging to the logged-in farmer."""
    fields = db.query(Field).filter(Field.user_id == current_user.user_id).all()
    return fields

@router.post("/", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
def create_field(
    req: FieldCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Use Case 3: Field Boundary Demarcation on Map (GeoJSON) - Table 4.3 in F26-201.
    Saves new parcel record with RFC 7946 GeoJSON boundary, computed acreage, and fallow cycle status.
    """
    field_id = f"fld_{uuid.uuid4().hex[:12]}"

    # Compute centroid if not provided
    center_lat = req.center_latitude
    center_lng = req.center_longitude
    if center_lat is None or center_lng is None:
        center_lat, center_lng = calculate_centroid(req.boundary_geojson)

    # 1 Acre = 4046.85642 Sq Meters
    area_sqm = req.area_sqm or round(req.area_acres * 4046.85642, 2)

    new_field = Field(
        field_id=field_id,
        user_id=current_user.user_id,
        field_name=req.field_name,
        shape_type=req.shape_type,
        area_acres=req.area_acres,
        area_sqm=area_sqm,
        boundary_geojson=req.boundary_geojson,
        center_latitude=center_lat,
        center_longitude=center_lng,
        current_cycle_id=None,  # Initially unstarted / fallow per SRS
    )
    db.add(new_field)
    db.commit()
    db.refresh(new_field)
    return new_field

@router.get("/{field_id}", response_model=FieldResponse)
def get_field_details(
    field_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch specific parcel details."""
    field = db.query(Field).filter(
        Field.field_id == field_id,
        Field.user_id == current_user.user_id
    ).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    return field

@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_field(
    field_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a farm parcel and cascade remove its cycles and observations."""
    field = db.query(Field).filter(
        Field.field_id == field_id,
        Field.user_id == current_user.user_id
    ).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    
    db.delete(field)
    db.commit()
    return None

