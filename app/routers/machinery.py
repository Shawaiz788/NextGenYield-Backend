from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.machinery import MachineryListing, MachineryBooking
from app.schemas.machinery import (
    MachineryListingCreate,
    MachineryListingResponse,
    MachineryBookingCreate,
    MachineryBookingResponse,
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
    """Book a time slot for machinery hire."""
    listing = db.query(MachineryListing).filter(MachineryListing.machinery_id == machinery_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Machinery listing not found.")
    
    if req.end_date <= req.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date.")
    
    # Calculate duration and pricing
    diff_seconds = (req.end_date - req.start_date).total_seconds()
    diff_days = max(1.0, round(diff_seconds / 86400.0, 1))
    
    if req.total_hours and listing.hourly_rate_pkr:
        total_amount = float(listing.hourly_rate_pkr) * req.total_hours
    else:
        total_amount = float(listing.daily_rate_pkr) * diff_days

    booking_id = f"book_{uuid.uuid4().hex[:8]}"
    booking = MachineryBooking(
        booking_id=booking_id,
        machinery_id=machinery_id,
        renter_id=current_user.user_id,
        start_date=req.start_date,
        end_date=req.end_date,
        total_hours=req.total_hours,
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
