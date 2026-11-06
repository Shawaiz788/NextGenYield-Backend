from typing import List, Tuple
from datetime import date, timedelta
import uuid
from app.models.schedule import FertilizerSchedule, IrrigationSchedule

def generate_default_schedules(cycle_id: str, sowing_date: date) -> Tuple[List[FertilizerSchedule], List[IrrigationSchedule]]:
    """
    Generates deterministic 140-day wheat agronomic schedules according to verified Punjab provincial protocol.
    Table 4.14 & Table 4.15 in F26-201 SRS.
    """
    # 3 Fertilizer splits
    fertilizers = [
        FertilizerSchedule(
            fertilizer_id=f"fert_{uuid.uuid4().hex[:12]}",
            cycle_id=cycle_id,
            split_number=1,
            nutrient_type="Basal DAP (Diammonium Phosphate) + SOP",
            target_das=0,
            dose_per_acre="1.0 Bag DAP (50kg) + 0.5 Bag SOP (25kg) / Acre",
            is_applied=True,  # Usually applied at sowing
            applied_at=None,
        ),
        FertilizerSchedule(
            fertilizer_id=f"fert_{uuid.uuid4().hex[:12]}",
            cycle_id=cycle_id,
            split_number=2,
            nutrient_type="1st Topdress Urea (Crown Root Initiation)",
            target_das=22,
            dose_per_acre="1.0 Bag Urea (50kg) / Acre with 1st irrigation",
            is_applied=False,
            applied_at=None,
        ),
        FertilizerSchedule(
            fertilizer_id=f"fert_{uuid.uuid4().hex[:12]}",
            cycle_id=cycle_id,
            split_number=3,
            nutrient_type="2nd Topdress Urea + Zinc Sulphate",
            target_das=55,
            dose_per_acre="0.5 Bag Urea (25kg) + 5kg Zinc (33%) / Acre",
            is_applied=False,
            applied_at=None,
        ),
    ]

    # 5 Key Irrigation milestones for irrigated wheat
    irrigations = [
        IrrigationSchedule(
            irrigation_id=f"irrig_{uuid.uuid4().hex[:12]}",
            cycle_id=cycle_id,
            event_name="1st CRI Irrigation (Crown Root)",
            water_source="Canal Water / Tube Well",
            target_das=22,
            is_completed=False,
        ),
        IrrigationSchedule(
            irrigation_id=f"irrig_{uuid.uuid4().hex[:12]}",
            cycle_id=cycle_id,
            event_name="2nd Tillering / Early Jointing Irrigation",
            water_source="Canal Water",
            target_das=45,
            is_completed=False,
        ),
        IrrigationSchedule(
            irrigation_id=f"irrig_{uuid.uuid4().hex[:12]}",
            cycle_id=cycle_id,
            event_name="3rd Booting / Spike Emergence Irrigation",
            water_source="Tube Well",
            target_das=75,
            is_completed=False,
        ),
        IrrigationSchedule(
            irrigation_id=f"irrig_{uuid.uuid4().hex[:12]}",
            cycle_id=cycle_id,
            event_name="4th Flowering / Anthesis Critical Irrigation",
            water_source="Canal Water",
            target_das=95,
            is_completed=False,
        ),
        IrrigationSchedule(
            irrigation_id=f"irrig_{uuid.uuid4().hex[:12]}",
            cycle_id=cycle_id,
            event_name="5th Grain Filling (Milky / Dough) Irrigation",
            water_source="Canal Water / Tube Well",
            target_das=115,
            is_completed=False,
        ),
    ]

    return fertilizers, irrigations

