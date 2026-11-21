from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean, Text
from datetime import datetime
from app.database import Base

class MarketplaceItem(Base):
    __tablename__ = "marketplace_items"

    item_id = Column(String(50), primary_key=True, index=True)
    seller_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    seller_name = Column(String(60), nullable=False)
    seller_phone = Column(String(20), nullable=False)
    title = Column(String(100), nullable=False)
    category = Column(String(40), nullable=False)  # seeds, fertilizer, machinery, wheat_grain, pesticides, land_lease, other
    price_pkr = Column(Numeric(12, 2), nullable=False)
    condition = Column(String(20), nullable=False, default="new")  # new, used, refurbished
    district = Column(String(50), nullable=False, index=True)
    location_address = Column(String(200), nullable=True)
    description = Column(Text, nullable=False)
    image_url = Column(String(255), nullable=True)
    is_sold = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
