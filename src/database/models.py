from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON, Float, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base

class Tenant(Base):
    """A paying customer who owns one or more groups."""
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    telegram_user_id = Column(BigInteger, unique=True, index=True)  # Admin's personal ID
    username = Column(String, nullable=True)
    subscription_tier = Column(String, default="free")  # free, shield, guard
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    groups = relationship("MonitoredGroup", back_populates="tenant")

class MonitoredGroup(Base):
    """A Telegram group/channel being protected."""
    __tablename__ = "monitored_groups"

    id = Column(BigInteger, primary_key=True, index=True)  # This is the Telegram Chat ID
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    title = Column(String)
    is_active = Column(Boolean, default=True)
    
    # JSON blob for flexible configuration (thresholds, enabled features)
    # This replaces config.yaml
    config = Column(JSON, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="groups")
    violations = relationship("ViolationLog", back_populates="group")
    messages = relationship("MessageLog", back_populates="group")

class ViolationLog(Base):
    """Record of a detected violation."""
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(BigInteger, ForeignKey("monitored_groups.id"))
    user_id = Column(BigInteger, index=True)
    username = Column(String, nullable=True)
    
    violation_type = Column(String, index=True)  # spam, raid, toxicity, fud
    content_type = Column(String)  # text, image, video
    confidence = Column(Float)
    reason = Column(String)
    action_taken = Column(String)  # deleted, warned, banned, none
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    group = relationship("MonitoredGroup", back_populates="violations")

class MessageLog(Base):
    """
    Log of recent messages for pattern detection (Raids/Spam).
    In production, this might move to Redis or be aggressively pruned.
    """
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(BigInteger, ForeignKey("monitored_groups.id"))
    user_id = Column(BigInteger, index=True)
    username = Column(String, nullable=True)
    
    content_hash = Column(String, index=True)  # MD5 of normalized text for spam matching
    message_length = Column(Integer)
    has_link = Column(Boolean, default=False)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    group = relationship("MonitoredGroup", back_populates="messages")

class ThreatPattern(Base):
    """Persistent record of detected complex threats (Raids, etc)."""
    __tablename__ = "threat_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(BigInteger, ForeignKey("monitored_groups.id"))
    
    pattern_type = Column(String) # coordinated_spam, raid, link_farm
    confidence = Column(Float)
    affected_user_count = Column(Integer)
    evidence = Column(JSON) # Snapshot of data that triggered it
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
