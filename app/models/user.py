from sqlalchemy import Column, String, DateTime
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True, index=True)
    full_name = Column(String(60), nullable=False)
    phone_number = Column(String(15), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="farmer")
    district = Column(String(50), nullable=False)
    language_pref = Column(String(5), nullable=False, default="en")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

