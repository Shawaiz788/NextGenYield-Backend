from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import math
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.field import Field
from app.models.machinery import MachineryListing
from app.models.marketplace import MarketplaceItem
from app.routers.fields import enrich_field_with_cycle
from app.models.community import (
    CommunityPost,
    PostComment,
    PostLike,
    UserConnection,
    ChatConversation,
    ChatMessage,
)
from app.schemas.community import (
    PostCreateRequest,
    PostResponse,
    CommentCreateRequest,
    CommentResponse,
    UserConnectionResponse,
    PaginatedFarmersResponse,
    MachinerySummary,
    MarketplaceItemSummary,
    PostSummary,
    PublicUserProfileResponse,
    SendMessageRequest,
    MessageResponse,
    ConversationResponse,
)
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/community", tags=["Community Social & Messaging"])

# --- POSTS & FEED ---

@router.get("/posts", response_model=List[PostResponse])
def get_community_feed(
    category: Optional[str] = Query(None, description="Filter posts by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve community posts feed with engagement statistics."""
    query = db.query(CommunityPost)
    if category and category != "all":
        query = query.filter(CommunityPost.category == category)
    
    posts = query.order_by(CommunityPost.created_at.desc()).limit(100).all()

    # Pre-fetch user's likes
    liked_post_ids = set(
        like.post_id for like in db.query(PostLike.post_id).filter(PostLike.user_id == current_user.user_id).all()
    )

    return [
        PostResponse(
            post_id=p.post_id,
            user_id=p.user_id,
            author_name=p.author_name,
            author_district=p.author_district,
            category=p.category,
            title=p.title,
            content=p.content,
            image_url=p.image_url,
            likes_count=p.likes_count,
            comments_count=p.comments_count,
            is_liked_by_me=p.post_id in liked_post_ids,
            created_at=p.created_at
        ) for p in posts
    ]

@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_community_post(
    req: PostCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish a new post to the community feed."""
    post_id = f"post_{uuid.uuid4().hex[:8]}"
    post = CommunityPost(
        post_id=post_id,
        user_id=current_user.user_id,
        author_name=current_user.full_name,
        author_district=current_user.district,
        category=req.category,
        title=req.title,
        content=req.content,
        image_url=req.image_url,
        likes_count=0,
        comments_count=0,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return PostResponse(
        post_id=post.post_id,
        user_id=post.user_id,
        author_name=post.author_name,
        author_district=post.author_district,
        category=post.category,
        title=post.title,
        content=post.content,
        image_url=post.image_url,
        likes_count=0,
        comments_count=0,
        is_liked_by_me=False,
        created_at=post.created_at
    )

@router.post("/posts/{post_id}/like")
def toggle_post_like(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle like / unlike on a post."""
    post = db.query(CommunityPost).filter(CommunityPost.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    existing_like = db.query(PostLike).filter(
        PostLike.post_id == post_id,
        PostLike.user_id == current_user.user_id
    ).first()

    if existing_like:
        db.delete(existing_like)
        post.likes_count = max(0, post.likes_count - 1)
        liked = False
    else:
        new_like = PostLike(
            like_id=f"like_{uuid.uuid4().hex[:8]}",
            post_id=post_id,
            user_id=current_user.user_id
        )
        db.add(new_like)
        post.likes_count += 1
        liked = True

    db.commit()
    return {"post_id": post_id, "liked": liked, "likes_count": post.likes_count}

@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
def get_post_comments(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve comments for a specific post."""
    comments = db.query(PostComment).filter(PostComment.post_id == post_id).order_by(PostComment.created_at.asc()).all()
    return [
        CommentResponse(
            comment_id=c.comment_id,
            post_id=c.post_id,
            user_id=c.user_id,
            author_name=c.author_name,
            content=c.content,
            created_at=c.created_at
        ) for c in comments
    ]

@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_post_comment(
    post_id: str,
    req: CommentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new comment to a community post."""
    post = db.query(CommunityPost).filter(CommunityPost.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    comment_id = f"cmt_{uuid.uuid4().hex[:8]}"
    comment = PostComment(
        comment_id=comment_id,
        post_id=post_id,
        user_id=current_user.user_id,
        author_name=current_user.full_name,
        content=req.content
    )
    db.add(comment)
    post.comments_count += 1
    db.commit()
    db.refresh(comment)
    return CommentResponse(
        comment_id=comment.comment_id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        author_name=comment.author_name,
        content=comment.content,
        created_at=comment.created_at
    )

# --- FARMER DISCOVERY & CONNECTIONS ---

@router.get("/farmers", response_model=PaginatedFarmersResponse)
def discover_farmers(
    search: Optional[str] = Query(None, description="Search by farmer name, district, phone, or role"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(8, ge=1, le=50, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Discover fellow wheat farmers and landowners with search and pagination."""
    query = db.query(User).filter(User.user_id != current_user.user_id)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (User.full_name.ilike(term)) |
            (User.district.ilike(term)) |
            (User.phone_number.ilike(term)) |
            (User.role.ilike(term))
        )

    total = query.count()
    total_pages = max(1, math.ceil(total / limit))
    offset = (page - 1) * limit
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    # Check existing connections
    connections = db.query(UserConnection).filter(
        (UserConnection.requester_id == current_user.user_id) |
        (UserConnection.target_id == current_user.user_id)
    ).all()

    conn_map = {}
    for c in connections:
        other_id = c.target_id if c.requester_id == current_user.user_id else c.requester_id
        conn_map[other_id] = (c.connection_id, c.status)

    items = []
    for u in users:
        conn_info = conn_map.get(u.user_id)
        items.append(UserConnectionResponse(
            connection_id=conn_info[0] if conn_info else f"none_{u.user_id}",
            user_id=u.user_id,
            full_name=u.full_name,
            district=u.district or "Punjab",
            role=u.role or "farmer",
            status=conn_info[1] if conn_info else "none",
            created_at=u.created_at
        ))

    return PaginatedFarmersResponse(
        items=items,
        total=total,
        page=page,
        total_pages=total_pages,
        limit=limit
    )

@router.post("/farmers/{target_user_id}/connect")
def connect_with_farmer(
    target_user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add or connect with another farmer."""
    if target_user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot connect with yourself.")
    
    existing = db.query(UserConnection).filter(
        ((UserConnection.requester_id == current_user.user_id) & (UserConnection.target_id == target_user_id)) |
        ((UserConnection.requester_id == target_user_id) & (UserConnection.target_id == current_user.user_id))
    ).first()

    if existing:
        return {"status": existing.status, "connection_id": existing.connection_id}

    conn = UserConnection(
        connection_id=f"conn_{uuid.uuid4().hex[:8]}",
        requester_id=current_user.user_id,
        target_id=target_user_id,
        status="accepted"
    )
    db.add(conn)
    db.commit()
    return {"status": "accepted", "connection_id": conn.connection_id}

@router.delete("/farmers/{target_user_id}/disconnect")
def disconnect_with_farmer(
    target_user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove friend connection with a farmer."""
    conn = db.query(UserConnection).filter(
        ((UserConnection.requester_id == current_user.user_id) & (UserConnection.target_id == target_user_id)) |
        ((UserConnection.requester_id == target_user_id) & (UserConnection.target_id == current_user.user_id))
    ).first()
    if conn:
        db.delete(conn)
        db.commit()
    return {"status": "none"}

@router.get("/users/{user_id}/profile", response_model=PublicUserProfileResponse)
def get_user_public_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve public farmer profile with authentic farm records and overview."""
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Farmer profile not found.")

    if target_user.user_id == current_user.user_id:
        conn_status = "self"
        conn_id = None
    else:
        conn = db.query(UserConnection).filter(
            ((UserConnection.requester_id == current_user.user_id) & (UserConnection.target_id == user_id)) |
            ((UserConnection.requester_id == user_id) & (UserConnection.target_id == current_user.user_id))
        ).first()
        conn_status = conn.status if conn else "none"
        conn_id = conn.connection_id if conn else None

    # Aggregate real fields and acreage
    raw_fields = db.query(Field).filter(Field.user_id == user_id).all()
    enriched_fields = [enrich_field_with_cycle(f, db) for f in raw_fields]
    for ef in enriched_fields:
        ef.owner_name = target_user.full_name
        ef.owner_district = target_user.district
        ef.owner_id = target_user.user_id
        ef.is_mine = (user_id == current_user.user_id)

    total_acres = round(sum(f.area_acres for f in raw_fields), 1) if raw_fields else 0.0
    active_crops_count = sum(1 for ef in enriched_fields if getattr(ef, 'has_active_cycle', False) or getattr(ef, 'cycle_status', '') == "active")

    # Real machinery listings
    raw_machinery = db.query(MachineryListing).filter(MachineryListing.owner_id == user_id).all()
    machinery_summaries = [
        MachinerySummary(
            machinery_id=m.machinery_id,
            title=m.title,
            machinery_type=m.machinery_type,
            daily_rate_pkr=float(m.daily_rate_pkr),
            hourly_rate_pkr=float(m.hourly_rate_pkr) if m.hourly_rate_pkr else None,
            district=m.district,
            is_available=m.is_available
        ) for m in raw_machinery
    ]

    # Real marketplace items
    raw_market = db.query(MarketplaceItem).filter(MarketplaceItem.seller_id == user_id).all()
    market_summaries = [
        MarketplaceItemSummary(
            item_id=it.item_id,
            title=it.title,
            category=it.category,
            price_pkr=float(it.price_pkr),
            condition=it.condition,
            is_sold=it.is_sold,
            image_url=it.image_url
        ) for it in raw_market
    ]

    # Real community posts
    raw_posts = db.query(CommunityPost).filter(CommunityPost.user_id == user_id).order_by(CommunityPost.created_at.desc()).limit(10).all()
    post_summaries = [
        PostSummary(
            post_id=p.post_id,
            title=p.title,
            category=p.category,
            likes_count=p.likes_count,
            comments_count=p.comments_count,
            created_at=p.created_at
        ) for p in raw_posts
    ]

    posts_count = db.query(CommunityPost).filter(CommunityPost.user_id == user_id).count()

    return PublicUserProfileResponse(
        user_id=target_user.user_id,
        full_name=target_user.full_name,
        district=target_user.district or "Punjab",
        role=target_user.role or "Progressive Wheat Farmer",
        phone_number=target_user.phone_number,
        total_fields=len(raw_fields),
        total_acreage=total_acres,
        active_crops_count=active_crops_count,
        posts_count=posts_count,
        machinery_count=len(raw_machinery),
        marketplace_count=len(raw_market),
        connection_status=conn_status,
        connection_id=conn_id,
        fields=enriched_fields,
        machinery=machinery_summaries,
        marketplace_items=market_summaries,
        recent_posts=post_summaries,
        created_at=target_user.created_at
    )

# --- DIRECT MESSAGING / CHAT ---

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List 1-on-1 chat threads for the current user."""
    convs = db.query(ChatConversation).filter(
        (ChatConversation.user1_id == current_user.user_id) |
        (ChatConversation.user2_id == current_user.user_id)
    ).order_by(ChatConversation.last_message_at.desc()).all()

    result = []
    for c in convs:
        other_user_id = c.user2_id if c.user1_id == current_user.user_id else c.user1_id
        other_user = db.query(User).filter(User.user_id == other_user_id).first()
        
        # Count unread messages sent to current_user
        unread = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == c.conversation_id,
            ChatMessage.sender_id == other_user_id,
            ChatMessage.is_read == False
        ).count()

        result.append(ConversationResponse(
            conversation_id=c.conversation_id,
            other_user_id=other_user_id,
            other_user_name=other_user.full_name if other_user else "Farmer",
            other_user_district=other_user.district if other_user else None,
            last_message=c.last_message,
            last_message_at=c.last_message_at,
            unread_count=unread
        ))
    return result

@router.post("/conversations/start", response_model=ConversationResponse)
def start_or_get_conversation(
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Find existing or start a new conversation with a target user."""
    target_id = req.recipient_id
    if not target_id:
        raise HTTPException(status_code=400, detail="recipient_id is required.")
    
    other_user = db.query(User).filter(User.user_id == target_id).first()
    if not other_user:
        raise HTTPException(status_code=404, detail="Target user not found.")

    conv = db.query(ChatConversation).filter(
        ((ChatConversation.user1_id == current_user.user_id) & (ChatConversation.user2_id == target_id)) |
        ((ChatConversation.user1_id == target_id) & (ChatConversation.user2_id == current_user.user_id))
    ).first()

    if not conv:
        conv = ChatConversation(
            conversation_id=f"conv_{uuid.uuid4().hex[:8]}",
            user1_id=current_user.user_id,
            user2_id=target_id,
            last_message=req.content,
            last_message_at=datetime.utcnow()
        )
        db.add(conv)
        db.flush()

    if req.content:
        msg = ChatMessage(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            conversation_id=conv.conversation_id,
            sender_id=current_user.user_id,
            content=req.content,
            is_read=False
        )
        db.add(msg)
        conv.last_message = req.content
        conv.last_message_at = datetime.utcnow()

    db.commit()
    return ConversationResponse(
        conversation_id=conv.conversation_id,
        other_user_id=other_user.user_id,
        other_user_name=other_user.full_name,
        other_user_district=other_user.district,
        last_message=conv.last_message,
        last_message_at=conv.last_message_at,
        unread_count=0
    )

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all messages in a conversation and mark as read."""
    conv = db.query(ChatConversation).filter(ChatConversation.conversation_id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    
    # Mark unread messages sent by other as read
    db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id,
        ChatMessage.sender_id != current_user.user_id,
        ChatMessage.is_read == False
    ).update({"is_read": True})
    db.commit()

    messages = db.query(ChatMessage).filter(ChatMessage.conversation_id == conversation_id).order_by(ChatMessage.created_at.asc()).all()
    sender_cache = {}
    result = []
    for m in messages:
        if m.sender_id not in sender_cache:
            u = db.query(User).filter(User.user_id == m.sender_id).first()
            sender_cache[m.sender_id] = u.full_name if u else "Farmer"
        result.append(MessageResponse(
            message_id=m.message_id,
            conversation_id=m.conversation_id,
            sender_id=m.sender_id,
            sender_name=sender_cache[m.sender_id],
            content=m.content,
            is_read=m.is_read,
            created_at=m.created_at
        ))
    return result

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    conversation_id: str,
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a direct message in an active conversation."""
    conv = db.query(ChatConversation).filter(ChatConversation.conversation_id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    msg = ChatMessage(
        message_id=msg_id,
        conversation_id=conversation_id,
        sender_id=current_user.user_id,
        content=req.content,
        is_read=False
    )
    db.add(msg)
    conv.last_message = req.content
    conv.last_message_at = datetime.utcnow()
    db.commit()
    db.refresh(msg)
    return MessageResponse(
        message_id=msg.message_id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        sender_name=current_user.full_name,
        content=msg.content,
        is_read=msg.is_read,
        created_at=msg.created_at
    )
