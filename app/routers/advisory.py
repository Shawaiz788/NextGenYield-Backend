import uuid
from datetime import timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.advisory import AgronomicAdvisoryRule, PeerShowcaseField, PeerShowcase
from app.schemas.advisory import (
    ShowcaseCreateRequest,
    PeerShowcaseResponse,
    AdvisoryRuleResponse,
)
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/advisory", tags=["Agronomic Advisory & Rules"])

@router.get("/rules", response_model=List[AdvisoryRuleResponse])
def get_all_advisory_rules(db: Session = Depends(get_db)):
    """
    Use Case 6: Retrieving Agronomic Advisory (Table 4.6 in F26-201).
    Returns deterministic agronomic guidance rules across all 6 phenological wheat stages.
    """
    rules = db.query(AgronomicAdvisoryRule).order_by(AgronomicAdvisoryRule.stage_index.asc()).all()
    return rules

@router.get("/rules/{stage_index}", response_model=AdvisoryRuleResponse)
def get_rule_by_stage(stage_index: int, db: Session = Depends(get_db)):
    """Fetch stage-specific deterministic advisory rule by index (0-5)."""
    rule = db.query(AgronomicAdvisoryRule).filter(
        AgronomicAdvisoryRule.stage_index == stage_index
    ).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No advisory rule defined for stage index {stage_index}"
        )
    return rule

showcase_router = APIRouter(prefix="/showcase", tags=["Peer Showcase & Benchmarks"])

@showcase_router.get("/", response_model=List[PeerShowcaseResponse])
def get_peer_benchmarks(db: Session = Depends(get_db)):
    """
    Use Case 9: Peer Showcase & Best-Practice Yield Benchmarks (Table 4.9 in F26-201).
    Returns verified top-yielding plots (54-62 Maunds/Acre).
    """
    benchmarks = db.query(PeerShowcaseField).order_by(PeerShowcaseField.yield_maunds_per_acre.desc()).all()
    return benchmarks

@showcase_router.get("/{showcase_id}", response_model=PeerShowcaseResponse)
def get_showcase_playbook(showcase_id: str, db: Session = Depends(get_db)):
    """Retrieve complete 140-day agronomic playbook for a verified peer field."""
    item = db.query(PeerShowcaseField).filter(PeerShowcaseField.showcase_id == showcase_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Showcase field not found")
    return item

@showcase_router.post("/", response_model=PeerShowcaseResponse, status_code=status.HTTP_201_CREATED)
def submit_peer_showcase(
    req: ShowcaseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Use Case 9: Peer Showcase & Best-Practice Yield Benchmarks (Table 4.9 in F26-201).
    Allows authenticated farmers to submit their verified harvest results and agronomic playbooks.
    """
    showcase_id = f"sc_{uuid.uuid4().hex[:10]}"
    
    # Determine region/district
    region_val = req.district or req.region or (current_user.district if hasattr(current_user, "district") and current_user.district else "Punjab")
    region_clean = "".join(ch for ch in region_val if ch.isalnum())
    region_slug = region_clean[:3].upper() if len(region_clean) >= 3 else "GEN"
    field_code = req.field_code or f"PK-{region_slug}-{uuid.uuid4().hex[:4].upper()}"

    # Metric yield calculation:
    # 1 Maund = 40 kg; 1 Acre = 4046.85642 m²
    actual_yield = req.actual_yield_maunds or req.yield_maunds_per_acre or 50.0
    yield_kg_sqm = req.yield_kg_sqm or round((actual_yield * 40.0) / 4046.85642, 2)

    # Harvest date fallback
    harvest_d = req.harvesting_date or req.harvest_date or (req.sowing_date + timedelta(days=140))

    # Format structured cycle_event_log
    event_log: List[Dict[str, Any]] = []
    if req.cycle_event_log:
        event_log = list(req.cycle_event_log)
    elif req.key_tactics:
        if isinstance(req.key_tactics, list):
            for i, item in enumerate(req.key_tactics):
                if isinstance(item, dict):
                    event_log.append(item)
                else:
                    event_log.append({"day": i * 20, "event": str(item)})
        elif isinstance(req.key_tactics, str):
            lines = [line.strip() for line in req.key_tactics.splitlines() if line.strip()]
            for i, line in enumerate(lines):
                event_log.append({"day": i * 20, "event": line})

    # Append submission metadata
    event_log.append({
        "title": req.title or req.field_name or f"{req.wheat_variety} Top Plot",
        "field_name": req.field_name or "",
        "photo_url": req.photo_url or "",
        "submitted_by_user_id": current_user.user_id,
        "submitted_by_name": current_user.full_name,
    })

    new_showcase = PeerShowcase(
        showcase_id=showcase_id,
        field_code=field_code,
        district=region_val,
        wheat_variety=req.wheat_variety,
        seed_company=req.seed_company or "Certified Local Seed",
        fertilizer_company=req.fertilizer_company or "FFC / Engro Standard",
        area_acres=req.area_acres or 1.0,
        shape_type=req.shape_type or "rectangle",
        yield_maunds_per_acre=actual_yield,
        yield_kg_sqm=yield_kg_sqm,
        sowing_date=req.sowing_date,
        harvest_date=harvest_d,
        cycle_event_log=event_log,
    )

    db.add(new_showcase)
    db.commit()
    db.refresh(new_showcase)
    return new_showcase
