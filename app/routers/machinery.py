from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import calendar
from datetime import datetime, timedelta, date

from app.database import get_db
from app.models.user import User
from app.models.machinery import MachineryListing, MachineryBooking
from app.schemas.machinery import (
    MachineryListingCreate,
    MachineryListingResponse,
    MachineryBookingCreate,
    MachineryBookingResponse,
    MachineryDailySlot,
    MachineryDayAvailability,
    MachineryScheduleResponse,
)
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/machinery", tags=["Machinery Rental & Booking"])

@router.get("/", response_model=List[MachineryListingResponse])
def list_machinery(
    machinery_type: Optional[str] = Query(None, description="Filter by machinery type (e.g. tractor, laser_leveler)"),
    district: Optional[str] = Query(None, description="Filter by district"),
    available_only: bool = Query(True, description="Only show available listings"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List available farm machinery for rent with optional filtering."""
    query = db.query(MachineryListing)
    if available_only:
        query = query.filter(MachineryListing.is_available == True)
    if machinery_type and machinery_type != "all":
        query = query.filter(MachineryListing.machinery_type == machinery_type)
    if district and district != "all":
        query = query.filter(MachineryListing.district.ilike(f"%{district}%"))
    
    listings = query.order_by(MachineryListing.created_at.desc()).all()
    
    # Attach bookings to each listing
    result = []
    for l in listings:
        bookings = db.query(MachineryBooking).filter(
            MachineryBooking.machinery_id == l.machinery_id,
            MachineryBooking.status.in_(["pending", "confirmed"])
        ).all()
        booking_res = [
            MachineryBookingResponse(
                booking_id=b.booking_id,
                machinery_id=b.machinery_id,
                renter_id=b.renter_id,
                start_date=b.start_date,
                end_date=b.end_date,
                total_hours=float(b.total_hours) if b.total_hours else None,
                total_amount_pkr=float(b.total_amount_pkr),
                status=b.status,
                purpose_step=b.purpose_step,
                notes=b.notes,
                created_at=b.created_at
            ) for b in bookings
        ]
        res = MachineryListingResponse(
            machinery_id=l.machinery_id,
            owner_id=l.owner_id,
            title=l.title,
            machinery_type=l.machinery_type,
            brand_model=l.brand_model,
            horsepower=float(l.horsepower) if l.horsepower else None,
            hourly_rate_pkr=float(l.hourly_rate_pkr) if l.hourly_rate_pkr else None,
            daily_rate_pkr=float(l.daily_rate_pkr),
            district=l.district,
            location_address=l.location_address,
            contact_phone=l.contact_phone,
            description=l.description,
            image_url=l.image_url,
            is_available=l.is_available,
            created_at=l.created_at,
            bookings=booking_res
        )
        result.append(res)
    return result

@router.post("/", response_model=MachineryListingResponse, status_code=status.HTTP_201_CREATED)
def create_machinery_listing(
    req: MachineryListingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Offer farm machinery for rent on the platform."""
    machinery_id = f"mach_{uuid.uuid4().hex[:8]}"
    listing = MachineryListing(
        machinery_id=machinery_id,
        owner_id=current_user.user_id,
        title=req.title,
        machinery_type=req.machinery_type,
        brand_model=req.brand_model,
        horsepower=req.horsepower,
        hourly_rate_pkr=req.hourly_rate_pkr,
        daily_rate_pkr=req.daily_rate_pkr,
        district=req.district,
        location_address=req.location_address,
        contact_phone=req.contact_phone,
        description=req.description,
        image_url=req.image_url,
        is_available=True,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return MachineryListingResponse(
        machinery_id=listing.machinery_id,
        owner_id=listing.owner_id,
        title=listing.title,
        machinery_type=listing.machinery_type,
        brand_model=listing.brand_model,
        horsepower=float(listing.horsepower) if listing.horsepower else None,
        hourly_rate_pkr=float(listing.hourly_rate_pkr) if listing.hourly_rate_pkr else None,
        daily_rate_pkr=float(listing.daily_rate_pkr),
        district=listing.district,
        location_address=listing.location_address,
        contact_phone=listing.contact_phone,
        description=listing.description,
        image_url=listing.image_url,
        is_available=listing.is_available,
        created_at=listing.created_at,
        bookings=[]
    )

@router.get("/user/my-listings", response_model=List[MachineryListingResponse])
def get_my_machinery_listings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve machinery listings posted by the current user."""
    listings = db.query(MachineryListing).filter(MachineryListing.owner_id == current_user.user_id).all()
    result = []
    for l in listings:
        bookings = db.query(MachineryBooking).filter(MachineryBooking.machinery_id == l.machinery_id).all()
        booking_res = [
            MachineryBookingResponse(
                booking_id=b.booking_id,
                machinery_id=b.machinery_id,
                renter_id=b.renter_id,
                start_date=b.start_date,
                end_date=b.end_date,
                total_hours=float(b.total_hours) if b.total_hours else None,
                total_amount_pkr=float(b.total_amount_pkr),
                status=b.status,
                purpose_step=b.purpose_step,
                notes=b.notes,
                created_at=b.created_at
            ) for b in bookings
        ]
        result.append(MachineryListingResponse(
            machinery_id=l.machinery_id,
            owner_id=l.owner_id,
            title=l.title,
            machinery_type=l.machinery_type,
            brand_model=l.brand_model,
            horsepower=float(l.horsepower) if l.horsepower else None,
            hourly_rate_pkr=float(l.hourly_rate_pkr) if l.hourly_rate_pkr else None,
            daily_rate_pkr=float(l.daily_rate_pkr),
            district=l.district,
            location_address=l.location_address,
            contact_phone=l.contact_phone,
            description=l.description,
            image_url=l.image_url,
            is_available=l.is_available,
            created_at=l.created_at,
            bookings=booking_res
        ))
    return result

@router.post("/{machinery_id}/book", response_model=MachineryBookingResponse, status_code=status.HTTP_201_CREATED)
def book_machinery_slot(
    machinery_id: str,
    req: MachineryBookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Book a time slot for machinery hire with mandatory 1-hour transit buffer enforcement."""
    listing = db.query(MachineryListing).filter(MachineryListing.machinery_id == machinery_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Machinery listing not found.")
    
    if req.end_date <= req.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date.")

    # 1-hour mandatory transit buffer between distinct bookings on the same machinery
    buffer_gap = timedelta(hours=1)
    existing_bookings = db.query(MachineryBooking).filter(
        MachineryBooking.machinery_id == machinery_id,
        MachineryBooking.status.in_(["pending", "confirmed"])
    ).all()

    for b in existing_bookings:
        # Check if requested slot overlaps with [b.start_date - buffer, b.end_date + buffer]
        if req.start_date < (b.end_date + buffer_gap) and req.end_date > (b.start_date - buffer_gap):
            raise HTTPException(
                status_code=400,
                detail=f"Requested slot ({req.start_date.strftime('%Y-%m-%d %H:%M')} - {req.end_date.strftime('%H:%M')}) conflicts with an existing booking ({b.start_date.strftime('%Y-%m-%d %H:%M')} - {b.end_date.strftime('%H:%M')}) or the mandatory 1-hour machinery transit buffer."
            )
    
    # Calculate duration and pricing
    diff_seconds = (req.end_date - req.start_date).total_seconds()
    diff_hours = round(diff_seconds / 3600.0, 1)
    diff_days = max(1.0, round(diff_seconds / 86400.0, 1))
    
    if req.total_hours and listing.hourly_rate_pkr:
        total_amount = float(listing.hourly_rate_pkr) * req.total_hours
    elif listing.hourly_rate_pkr and diff_hours < 8.0:
        total_amount = float(listing.hourly_rate_pkr) * diff_hours
    else:
        total_amount = float(listing.daily_rate_pkr) * diff_days

    booking_id = f"book_{uuid.uuid4().hex[:8]}"
    booking = MachineryBooking(
        booking_id=booking_id,
        machinery_id=machinery_id,
        renter_id=current_user.user_id,
        start_date=req.start_date,
        end_date=req.end_date,
        total_hours=req.total_hours or diff_hours,
        total_amount_pkr=round(total_amount, 2),
        status="confirmed",
        purpose_step=req.purpose_step,
        notes=req.notes
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return MachineryBookingResponse(
        booking_id=booking.booking_id,
        machinery_id=booking.machinery_id,
        renter_id=booking.renter_id,
        start_date=booking.start_date,
        end_date=booking.end_date,
        total_hours=float(booking.total_hours) if booking.total_hours else None,
        total_amount_pkr=float(booking.total_amount_pkr),
        status=booking.status,
        purpose_step=booking.purpose_step,
        notes=booking.notes,
        created_at=booking.created_at
    )

@router.get("/{machinery_id}/schedule", response_model=MachineryScheduleResponse)
def get_machinery_schedule(
    machinery_id: str,
    month: Optional[str] = Query(None, description="Month in YYYY-MM format, e.g. 2026-11"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve monthly calendar availability and daily time slots with 1-hour transit buffers."""
    listing = db.query(MachineryListing).filter(MachineryListing.machinery_id == machinery_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Machinery listing not found.")

    today = date.today()
    if month and len(month) == 7 and "-" in month:
        try:
            year, m_num = int(month.split("-")[0]), int(month.split("-")[1])
        except ValueError:
            year, m_num = today.year, today.month
    else:
        year, m_num = today.year, today.month

    target_month_str = f"{year:04d}-{m_num:02d}"
    num_days = calendar.monthrange(year, m_num)[1]

    # Query all active bookings spanning this month
    month_start = datetime(year, m_num, 1, 0, 0, 0)
    month_end = datetime(year, m_num, num_days, 23, 59, 59)

    bookings = db.query(MachineryBooking).filter(
        MachineryBooking.machinery_id == machinery_id,
        MachineryBooking.status.in_(["pending", "confirmed"]),
        MachineryBooking.start_date <= month_end,
        MachineryBooking.end_date >= month_start
    ).all()

    buffer_gap = timedelta(hours=1)
    hourly_rate = float(listing.hourly_rate_pkr) if listing.hourly_rate_pkr else round(float(listing.daily_rate_pkr) / 8.0, 2)
    daily_rate = float(listing.daily_rate_pkr)

    # Standard daily slots: Morning (08:00-12:00), Afternoon (13:00-17:00), Evening (18:00-21:00), Full Day (08:00-18:00)
    slot_defs = [
        {"slot_id": "morning", "label_en": "Morning Slot (8 AM - 12 PM)", "label_ur": "صبح کا وقت (8 تا 12)", "start": (8, 0), "end": (12, 0), "hours": 4.0, "price": round(hourly_rate * 4.0, 2)},
        {"slot_id": "afternoon", "label_en": "Afternoon Slot (1 PM - 5 PM)", "label_ur": "دوپہر کا وقت (1 تا 5)", "start": (13, 0), "end": (17, 0), "hours": 4.0, "price": round(hourly_rate * 4.0, 2)},
        {"slot_id": "evening", "label_en": "Evening Slot (6 PM - 9 PM)", "label_ur": "شام کا وقت (6 تا 9)", "start": (18, 0), "end": (21, 0), "hours": 3.0, "price": round(hourly_rate * 3.0, 2)},
        {"slot_id": "full_day", "label_en": "Full Working Day (8 AM - 6 PM)", "label_ur": "مکمل دن (8 تا 6)", "start": (8, 0), "end": (18, 0), "hours": 10.0, "price": daily_rate},
    ]

    days_availability: List[MachineryDayAvailability] = []

    for d in range(1, num_days + 1):
        day_date = date(year, m_num, d)
        date_str = f"{year:04d}-{m_num:02d}-{d:02d}"
        is_past = day_date < today

        day_slots: List[MachineryDailySlot] = []
        regular_slots_booked = 0

        for s_def in slot_defs:
            s_start = datetime(year, m_num, d, s_def["start"][0], s_def["start"][1])
            s_end = datetime(year, m_num, d, s_def["end"][0], s_def["end"][1])

            # Check overlap with existing bookings + buffer
            is_avail = not is_past
            if is_avail:
                for b in bookings:
                    if s_start < (b.end_date + buffer_gap) and s_end > (b.start_date - buffer_gap):
                        is_avail = False
                        break

            if s_def["slot_id"] in ["morning", "afternoon", "evening"] and not is_avail:
                regular_slots_booked += 1

            day_slots.append(MachineryDailySlot(
                slot_id=s_def["slot_id"],
                label_en=s_def["label_en"],
                label_ur=s_def["label_ur"],
                start_time=f"{s_def['start'][0]:02d}:{s_def['start'][1]:02d}",
                end_time=f"{s_def['end'][0]:02d}:{s_def['end'][1]:02d}",
                duration_hours=s_def["hours"],
                is_available=is_avail,
                price_pkr=s_def["price"]
            ))

        # Full day is only available if all 3 partial slots are available
        for s in day_slots:
            if s.slot_id == "full_day" and regular_slots_booked > 0:
                s.is_available = False

        if is_past:
            day_status = "past"
            is_fully_booked = True
        elif regular_slots_booked >= 3:
            day_status = "fully_booked"
            is_fully_booked = True
        else:
            day_status = "available"
            is_fully_booked = False

        days_availability.append(MachineryDayAvailability(
            date=date_str,
            day_status=day_status,
            is_fully_booked=is_fully_booked,
            slots=day_slots
        ))

    return MachineryScheduleResponse(
        machinery_id=machinery_id,
        month=target_month_str,
        days=days_availability
    )

@router.get("/user/my-bookings", response_model=List[MachineryBookingResponse])
def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve bookings requested by the current user."""
    bookings = db.query(MachineryBooking).filter(MachineryBooking.renter_id == current_user.user_id).order_by(MachineryBooking.created_at.desc()).all()
    return [
        MachineryBookingResponse(
            booking_id=b.booking_id,
            machinery_id=b.machinery_id,
            renter_id=b.renter_id,
            start_date=b.start_date,
            end_date=b.end_date,
            total_hours=float(b.total_hours) if b.total_hours else None,
            total_amount_pkr=float(b.total_amount_pkr),
            status=b.status,
            purpose_step=b.purpose_step,
            notes=b.notes,
            created_at=b.created_at
        ) for b in bookings
    ]
