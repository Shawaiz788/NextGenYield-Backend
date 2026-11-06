from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
import re

def normalize_phone_number(v: str) -> str:
    """Normalize farmer phone number to clean string."""
    cleaned = re.sub(r"[^\d+]", "", v)
    if cleaned.startswith("+92"):
        cleaned = "0" + cleaned[3:]
    elif cleaned.startswith("92") and len(cleaned) == 12:
        cleaned = "0" + cleaned[2:]
    return cleaned

class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=60, description="Full farmer name")
    phone_number: str = Field(..., description="Mobile number for login and alerts")
    password: str = Field(..., min_length=4, max_length=64, description="PIN or password")
    role: str = Field("farmer", description="farmer, landowner, or stakeholder")
    district: str = Field("Faisalabad", max_length=50, description="Administrative district")
    language_pref: str = Field("en", description="'en' or 'ur'")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        norm = normalize_phone_number(v)
        if len(norm) < 10 or len(norm) > 15:
            raise ValueError("Invalid phone number length")
        return norm

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("farmer", "landowner", "stakeholder"):
            raise ValueError("Role must be one of: farmer, landowner, stakeholder")
        return v

    @field_validator("language_pref")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        if v not in ("en", "ur"):
            raise ValueError("Language preference must be 'en' or 'ur'")
        return v

class UserLoginRequest(BaseModel):
    phone_number: str = Field(..., description="Registered mobile number")
    password: str = Field(..., description="PIN or password")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_phone_number(v)

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    full_name: str
    phone_number: str
    role: str
    district: str
    language_pref: str
    created_at: datetime

class UserUpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=60)
    district: Optional[str] = Field(None, max_length=50)
    language_pref: Optional[str] = Field(None, pattern="^(en|ur)$")

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse
