from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean, Text
from datetime import datetime
from app.database import Base

class MachineryListing(Base):
    __tablename__ = "machinery_listings"

    machinery_id = Column(String(50), primary_key=True, index=True)
    owner_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    machinery_type = Column(String(40), nullable=False)  # tractor, laser_leveler, rotavator, seed_drill, chisel_plow, combine_harvester, disc_harrow
    brand_model = Column(String(80), nullable=True)     # e.g. Massey Ferguson 385, Millat
    horsepower = Column(Numeric(6, 1), nullable=True)    # e.g. 85.0
    hourly_rate_pkr = Column(Numeric(10, 2), nullable=True)
    daily_rate_pkr = Column(Numeric(10, 2), nullable=False)
    district = Column(String(50), nullable=False, index=True)
    location_address = Column(String(200), nullable=True)
    contact_phone = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    is_available = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class MachineryBooking(Base):
    __tablename__ = "machinery_bookings"

    booking_id = Column(String(50), primary_key=True, index=True)
    machinery_id = Column(String(50), ForeignKey("machinery_listings.machinery_id", ondelete="CASCADE"), nullable=False, index=True)
    renter_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_hours = Column(Numeric(6, 1), nullable=True)
    total_amount_pkr = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, confirmed, in_progress, completed, cancelled
    purpose_step = Column(String(50), nullable=True)  # laser_leveling, plowing, rauni, rotavating, sowing
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
