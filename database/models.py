from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import datetime
from database.connection import Base

class User(Base):
    """Local dashboard user profile for dashboard access control."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)  # Local dashboard portal password
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")

class Account(Base):
    """Stored credentials and targets for external monitored websites."""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform_name = Column(String, nullable=False)   # e.g., 'GitHub', 'ITU Portal'
    target_url = Column(String, nullable=False)      # The exact notifications view URL
    username = Column(String, nullable=False)        # Target site username/email
    encrypted_password = Column(Text, nullable=False) # Protected AES cipher block string
    
    # State flags tracking update notifications
    has_update = Column(Boolean, default=False)
    last_checked = Column(DateTime, nullable=True)
    last_update_summary = Column(Text, nullable=True) # Text snapshot of last known state

    user = relationship("User", back_populates="accounts")
    logs = relationship("UpdateLog", back_populates="account", cascade="all, delete-orphan")

class UpdateLog(Base):
    """Historical timeline capture of delta platform updates found by the engine."""
    __tablename__ = "update_logs"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, nullable=False)          # 'SUCCESS', 'CHANGED', 'AUTH_ERROR', 'FETCH_FAILED'
    details = Column(Text, nullable=True)            # Description of parsed data alterations

    account = relationship("Account", back_populates="logs")