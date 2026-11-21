from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Text
from datetime import datetime
from app.database import Base

class CommunityPost(Base):
    __tablename__ = "community_posts"

    post_id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    author_name = Column(String(60), nullable=False)
    author_district = Column(String(50), nullable=False)
    category = Column(String(30), nullable=False, default="general")  # agronomy_tips, disease_alert, machinery, market_prices, general
    title = Column(String(120), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(255), nullable=True)
    likes_count = Column(Integer, nullable=False, default=0)
    comments_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class PostComment(Base):
    __tablename__ = "post_comments"

    comment_id = Column(String(50), primary_key=True, index=True)
    post_id = Column(String(50), ForeignKey("community_posts.post_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    author_name = Column(String(60), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class PostLike(Base):
    __tablename__ = "post_likes"

    like_id = Column(String(50), primary_key=True, index=True)
    post_id = Column(String(50), ForeignKey("community_posts.post_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class UserConnection(Base):
    __tablename__ = "user_connections"

    connection_id = Column(String(50), primary_key=True, index=True)
    requester_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="accepted")  # pending, accepted, blocked
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    conversation_id = Column(String(50), primary_key=True, index=True)
    user1_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    user2_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    last_message = Column(Text, nullable=True)
    last_message_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(String(50), primary_key=True, index=True)
    conversation_id = Column(String(50), ForeignKey("chat_conversations.conversation_id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
