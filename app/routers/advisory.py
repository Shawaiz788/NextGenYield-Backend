from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.advisory import AgronomicAdvisoryRule, PeerShowcaseField
from app.schemas.observation import AdvisoryRuleResponse, PeerShowcaseResponse

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

