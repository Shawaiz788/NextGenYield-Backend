from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid
from app.database import get_db
from app.models.user import User
from app.models.field import Field
from app.models.crop_cycle import CropCycle
from app.models.observation import FieldObservation
from app.models.employee import FarmEmployee, FieldAssignment
from app.schemas.field import (
    FieldCreateRequest,
    FieldUpdateRequest,
    FieldResponse,
    MAX_FIELD_ACRES,
    MAX_FIELD_SQM,
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

def enrich_field_with_cycle(f: Field, db: Session) -> Field:
    """Dynamically hydrate active crop cycle details onto the field parcel response."""
    f.cycle_status = "not_started"
    f.current_stage_index = 0
    f.days_after_sowing = None
    f.wheat_variety = None
    f.seed_company = None
    f.fertilizer_company = None
    f.sowing_date = None
    f.target_harvest_date = None

    cycle = None
    if f.current_cycle_id:
        cycle = db.query(CropCycle).filter(CropCycle.cycle_id == f.current_cycle_id).first()
    if not cycle:
        cycle = (
            db.query(CropCycle)
            .filter(CropCycle.field_id == f.field_id, CropCycle.is_active == True)
            .order_by(CropCycle.created_at.desc())
            .first()
        )

    if cycle and cycle.is_active:
        f.current_cycle_id = cycle.cycle_id
        f.wheat_variety = cycle.wheat_variety
        f.seed_company = cycle.seed_company
        f.fertilizer_company = cycle.fertilizer_company
        f.sowing_date = cycle.sowing_date
        f.target_harvest_date = cycle.target_harvest_date
        f.cycle_status = "active"

        if cycle.sowing_date:
            das = max(1, (datetime.now().date() - cycle.sowing_date).days + 1)
            f.days_after_sowing = min(das, 140)

            # Check if there is an AI observation for this cycle
            obs = (
                db.query(FieldObservation)
                .filter(FieldObservation.cycle_id == cycle.cycle_id)
                .order_by(FieldObservation.captured_at.desc())
                .first()
            )
            if obs:
                f.current_stage_index = obs.stage_index
            else:
                if das <= 35:
                    f.current_stage_index = 0
                elif das <= 65:
                    f.current_stage_index = 1
                elif das <= 85:
                    f.current_stage_index = 2
                elif das <= 105:
                    f.current_stage_index = 3
                elif das <= 125:
                    f.current_stage_index = 4
                else:
                    f.current_stage_index = 5
    return f

@router.get("/", response_model=List[FieldResponse])
def get_user_fields(
    include_community: bool = Query(False, description="Include community neighbor fields on the map"),
    user_id: Optional[str] = Query(None, description="Filter fields by a specific farmer"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all demarcated farm parcels belonging to the user, specific farmer, or community map."""
    if user_id:
        target_user = db.query(User).filter(User.user_id == user_id).first()
        if not target_user:
            return []
        target_fields = db.query(Field).filter(Field.user_id == user_id).all()
        enriched = []
        for f in target_fields:
            ef = enrich_field_with_cycle(f, db)
            ef.owner_id = target_user.user_id
            ef.owner_name = target_user.full_name
            ef.owner_district = target_user.district
            ef.is_mine = (target_user.user_id == current_user.user_id)
            enriched.append(ef)
        return enriched

    owned_fields = db.query(Field).filter(Field.user_id == current_user.user_id).all()
    field_dict = {f.field_id: f for f in owned_fields}

    # Check if current user is delegated any fields as an employee
    emp_records = db.query(FarmEmployee).filter(
        (FarmEmployee.employee_user_id == current_user.user_id) |
        (FarmEmployee.employee_phone == current_user.phone_number)
    ).all()

    for emp in emp_records:
        if emp.access_all_fields:
            owner_fields = db.query(Field).filter(Field.user_id == emp.owner_id).all()
            for f in owner_fields:
                field_dict[f.field_id] = f
        else:
            assignments = db.query(FieldAssignment).filter(FieldAssignment.employee_record_id == emp.employee_record_id).all()
            for a in assignments:
                if a.field_id not in field_dict:
                    f = db.query(Field).filter(Field.field_id == a.field_id).first()
                    if f:
                        field_dict[f.field_id] = f

    result = []
    for f in field_dict.values():
        ef = enrich_field_with_cycle(f, db)
        ef.owner_id = current_user.user_id
        ef.owner_name = current_user.full_name
        ef.owner_district = current_user.district
        ef.is_mine = True
        result.append(ef)

    if include_community:
        # Retrieve neighbor / community fields from other registered farmers
        owned_keys = list(field_dict.keys())
        comm_query = db.query(Field)
        if owned_keys:
            comm_query = comm_query.filter(~Field.field_id.in_(owned_keys))
        comm_fields = comm_query.order_by(Field.created_at.desc()).limit(30).all()

        user_cache = {}
        for cf in comm_fields:
            if cf.user_id not in user_cache:
                user_cache[cf.user_id] = db.query(User).filter(User.user_id == cf.user_id).first()
            owner = user_cache[cf.user_id]
            ef = enrich_field_with_cycle(cf, db)
            ef.owner_id = cf.user_id
            ef.owner_name = owner.full_name if owner else "Punjab Farmer"
            ef.owner_district = owner.district if owner else "Faisalabad"
            ef.is_mine = False
            result.append(ef)

    return result

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
    area_acres = round(req.area_acres, 2)
    area_sqm = round(req.area_sqm or (area_acres * 4046.85642), 2)
    if area_acres > MAX_FIELD_ACRES or area_sqm > MAX_FIELD_SQM:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Field area ({area_acres:,.2f} acres) exceeds the maximum allowed limit of {MAX_FIELD_ACRES:,.0f} acres. Please demarcate a smaller farm parcel.",
        )

    # Determine city/district code from user profile
    district_clean = (current_user.district or "FSD").split("/")[0].strip().upper()
    city_code = "LHR" if "LAHORE" in district_clean else (
        "FSD" if "FAISALABAD" in district_clean else (
            "MLT" if "MULTAN" in district_clean else (
                "SWL" if "SAHIWAL" in district_clean else district_clean[:3]
            )
        )
    )

    # Calculate sequential number for user's field in this region (1, 2, 3...)
    existing_count = db.query(Field).filter(Field.user_id == current_user.user_id).count()
    field_code = f"PK-{city_code}-{str(existing_count + 1).zfill(2)}"

    new_field = Field(
        field_id=field_id,
        field_code=field_code,
        user_id=current_user.user_id,
        field_name=req.field_name,
        shape_type=req.shape_type,
        area_acres=area_acres,
        area_sqm=area_sqm,
        boundary_geojson=req.boundary_geojson,
        center_latitude=center_lat,
        center_longitude=center_lng,
        current_cycle_id=None,  # Initially unstarted / fallow per SRS
    )
    db.add(new_field)
    db.commit()
    db.refresh(new_field)
    return enrich_field_with_cycle(new_field, db)

@router.get("/{field_id}", response_model=FieldResponse)
def get_field_details(
    field_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch specific parcel details."""
    field = db.query(Field).filter(Field.field_id == field_id).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    
    if field.user_id != current_user.user_id:
        # Check if delegated to employee
        emp = db.query(FarmEmployee).filter(
            ((FarmEmployee.employee_user_id == current_user.user_id) |
             (FarmEmployee.employee_phone == current_user.phone_number)),
            FarmEmployee.owner_id == field.user_id
        ).first()
        if not emp:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        if not emp.access_all_fields:
            assignment = db.query(FieldAssignment).filter(
                FieldAssignment.employee_record_id == emp.employee_record_id,
                FieldAssignment.field_id == field_id
            ).first()
            if not assignment:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Field not assigned to you")
    return enrich_field_with_cycle(field, db)

@router.put("/{field_id}", response_model=FieldResponse)
def update_field(
    field_id: str,
    req: FieldUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update farm parcel attributes (name, area, shape, boundary, coordinates, soil texture).
    Verifies that the logged-in farmer owns the field.
    """
    field = db.query(Field).filter(Field.field_id == field_id).first()
    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field with ID '{field_id}' not found"
        )

    if field.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to modify this field parcel"
        )

    # 1. Update name
    if req.field_name is not None:
        field.field_name = req.field_name

    # 2. Update shape type
    if req.shape_type is not None:
        field.shape_type = req.shape_type

    # 3. Handle boundary GeoJSON, coordinates, and soil texture
    bg = dict(field.boundary_geojson or {})
    boundary_changed = False

    if req.boundary_geojson is not None:
        bg = dict(req.boundary_geojson)
        boundary_changed = True
    elif req.coordinates is not None:
        coords = req.coordinates
        # Wrap single ring [[lng, lat], ...] to GeoJSON Polygon rings [[[lng, lat], ...]]
        if coords and isinstance(coords[0], list) and isinstance(coords[0][0], (int, float)):
            coords = [coords]
        bg["type"] = "Polygon"
        bg["coordinates"] = coords
        boundary_changed = True

    # Handle soil texture in GeoJSON properties
    if req.soil_texture is not None:
        props = dict(bg.get("properties") or {})
        props["soil_texture"] = req.soil_texture
        bg["properties"] = props
        boundary_changed = True

    if boundary_changed:
        field.boundary_geojson = bg

    # 4. Update area
    if req.area_acres is not None:
        field.area_acres = req.area_acres
        field.area_sqm = req.area_sqm or round(req.area_acres * 4046.85642, 2)
    elif req.area_sqm is not None:
        field.area_sqm = req.area_sqm
        field.area_acres = round(req.area_sqm / 4046.85642, 2)

    # 5. Centroid recalculation
    if req.center_latitude is not None and req.center_longitude is not None:
        field.center_latitude = req.center_latitude
        field.center_longitude = req.center_longitude
    elif boundary_changed and field.boundary_geojson:
        lat, lng = calculate_centroid(field.boundary_geojson)
        field.center_latitude = lat
        field.center_longitude = lng
    elif req.center_latitude is not None:
        field.center_latitude = req.center_latitude
    elif req.center_longitude is not None:
        field.center_longitude = req.center_longitude

    db.commit()
    db.refresh(field)
    return enrich_field_with_cycle(field, db)

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

    if field.current_cycle_id is not None:
        field.current_cycle_id = None
        db.flush()

    db.delete(field)
    db.commit()
    return None

