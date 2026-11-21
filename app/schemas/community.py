from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, ForwardRef
from datetime import datetime
from app.schemas.field import FieldResponse

class PostCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., max_length=120)
    category: str = Field("general", max_length=30)  # agronomy_tips, disease_alert, machinery, market_prices, general
    content: str
    image_url: Optional[str] = None

class CommentCreateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content: str

class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comment_id: str
    post_id: str
    user_id: str
    author_name: str
    content: str
    created_at: datetime

class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post_id: str
    user_id: str
    author_name: str
    author_district: str
    category: str
    title: str
    content: str
    image_url: Optional[str] = None
    likes_count: int
    comments_count: int
    is_liked_by_me: Optional[bool] = False
    created_at: datetime

class UserConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    connection_id: str
    user_id: str
    full_name: str
    district: str
    role: str
    status: str
    created_at: datetime

class PaginatedFarmersResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[UserConnectionResponse]
    total: int
    page: int
    total_pages: int
    limit: int

class MachinerySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    machinery_id: str
    title: str
    machinery_type: str
    daily_rate_pkr: float
    hourly_rate_pkr: Optional[float] = None
    district: str
    is_available: bool

class MarketplaceItemSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: str
    title: str
    category: str
    price_pkr: float
    condition: str
    is_sold: bool
    image_url: Optional[str] = None

class PostSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post_id: str
    title: str
    category: str
    likes_count: int
    comments_count: int
    created_at: datetime

class PublicUserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    full_name: str
    district: str
    role: str
    phone_number: Optional[str] = None
    total_fields: int = 0
    total_acreage: float = 0.0
    active_crops_count: int = 0
    posts_count: int = 0
    machinery_count: int = 0
    marketplace_count: int = 0
    connection_status: str = "none"  # "none", "pending", "accepted", "self"
    connection_id: Optional[str] = None
    fields: List[FieldResponse] = []
    machinery: List[MachinerySummary] = []
    marketplace_items: List[MarketplaceItemSummary] = []
    recent_posts: List[PostSummary] = []
    created_at: datetime

class SendMessageRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recipient_id: Optional[str] = None
    content: str

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    conversation_id: str
    sender_id: str
    sender_name: Optional[str] = None
    content: str
    is_read: bool
    created_at: datetime

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: str
    other_user_id: str
    other_user_name: str
    other_user_district: Optional[str] = None
    last_message: Optional[str] = None
    last_message_at: datetime
    unread_count: int = 0
