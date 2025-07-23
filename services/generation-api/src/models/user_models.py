"""
User models for authentication, authorization, and user management
Supporting role-based access control and user preferences
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from enum import Enum

from ..core.database import Base


class UserRole(str, Enum):
    """Enumeration of user roles."""
    ADMIN = "admin"
    DESIGNER = "designer"
    BRAND_MANAGER = "brand_manager"
    VIEWER = "viewer"
    API_CLIENT = "api_client"


class SubscriptionTier(str, Enum):
    """Enumeration of subscription tiers."""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class User(Base):
    """User model for authentication and profile management."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    display_name = Column(String(200))
    bio = Column(Text)
    avatar_url = Column(String(500))
    
    # Role and permissions
    role = Column(String(50), default="viewer")  # UserRole enum
    permissions = Column(JSON, default=list)  # Specific permissions
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Subscription and usage
    subscription_tier = Column(String(50), default="free")  # SubscriptionTier enum
    subscription_expires = Column(DateTime(timezone=True))
    api_quota_limit = Column(Integer, default=100)  # Monthly API calls
    api_quota_used = Column(Integer, default=0)
    
    # Preferences
    preferences = Column(JSON, default=dict)  # User preferences and settings
    notification_settings = Column(JSON, default=dict)
    ui_settings = Column(JSON, default=dict)
    
    # Brand associations
    primary_brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    accessible_brands = Column(ARRAY(String))  # Brand IDs user can access
    
    # Activity tracking
    last_login = Column(DateTime(timezone=True))
    last_activity = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime(timezone=True))
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime(timezone=True))
    email_verification_token = Column(String(255))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    generation_jobs = relationship("GenerationJob", back_populates="user")
    feedback = relationship("GenerationFeedback", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")


class APIKey(Base):
    """API key management for programmatic access."""
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Key information
    name = Column(String(255), nullable=False)  # User-friendly name
    key_hash = Column(String(255), nullable=False, unique=True)  # Hashed API key
    key_prefix = Column(String(20), nullable=False)  # Visible prefix for identification
    
    # Permissions and limitations
    permissions = Column(JSON, default=list)  # Specific API permissions
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    quota_limit = Column(Integer, default=10000)  # Monthly quota
    quota_used = Column(Integer, default=0)
    
    # Restrictions
    allowed_ips = Column(ARRAY(String))  # IP whitelist
    allowed_domains = Column(ARRAY(String))  # Domain whitelist
    
    # Status and lifecycle
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    last_used = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class UserSession(Base):
    """User session tracking for security and analytics."""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session information
    session_token = Column(String(255), nullable=False, unique=True)
    refresh_token = Column(String(255), unique=True)
    
    # Client information
    user_agent = Column(Text)
    ip_address = Column(String(45))  # IPv6 compatible
    device_info = Column(JSON)
    location = Column(JSON)  # Geo-location data
    
    # Session lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    # Security flags
    is_suspicious = Column(Boolean, default=False)
    security_flags = Column(JSON, default=list)


class UserActivity(Base):
    """User activity logging for analytics and auditing."""
    __tablename__ = "user_activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"))
    
    # Activity details
    activity_type = Column(String(100), nullable=False)  # login, generation, view, etc.
    activity_description = Column(String(500))
    resource_type = Column(String(100))  # brand, collection, product, etc.
    resource_id = Column(String(255))  # ID of the resource
    
    # Request information
    endpoint = Column(String(255))  # API endpoint or page
    method = Column(String(10))  # HTTP method
    status_code = Column(Integer)  # Response status
    
    # Performance metrics
    response_time = Column(Float)  # Response time in seconds
    data_size = Column(Integer)  # Response size in bytes
    
    # Context
    context_data = Column(JSON)  # Additional context information
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserPreference(Base):
    """Detailed user preferences for personalization."""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Preference identification
    category = Column(String(100), nullable=False)  # ui, generation, notifications
    key = Column(String(255), nullable=False)
    value = Column(JSON, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        {"schema": None}  # Ensure unique combination of user_id, category, key
    )


class UserNotification(Base):
    """User notification system."""
    __tablename__ = "user_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(100))  # info, success, warning, error
    
    # Categorization
    category = Column(String(100))  # generation, system, billing, etc.
    priority = Column(String(50), default="normal")  # low, normal, high, urgent
    
    # Status
    is_read = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    
    # Action information
    action_url = Column(String(500))  # URL for related action
    action_data = Column(JSON)  # Additional action data
    
    # Delivery
    delivery_methods = Column(ARRAY(String))  # email, push, in_app
    delivered_at = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # Auto-cleanup date