from datetime import datetime, timedelta
from typing import Optional, Any, Union
import jwt
import bcrypt
from app.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password/PIN against its bcrypt hash."""
    if isinstance(plain_password, str):
        plain_password_bytes = plain_password.encode("utf-8")
    else:
        plain_password_bytes = plain_password

    if isinstance(hashed_password, str):
        hashed_password_bytes = hashed_password.encode("utf-8")
    else:
        hashed_password_bytes = hashed_password

    # Truncate to 72 bytes per bcrypt standard specification
    plain_password_bytes = plain_password_bytes[:72]
    return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)

def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for a plain password or PIN."""
    if isinstance(password, str):
        password_bytes = password.encode("utf-8")
    else:
        password_bytes = password
    # Truncate to 72 bytes per bcrypt standard specification
    password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT access token for mobile/web sessions."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
