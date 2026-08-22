from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

from backend.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(200), nullable=False)
    owner_name = Column(String(200), nullable=False)
    email = Column(String(320), unique=True, index=True, nullable=False)

    password_hash = Column(String(255), nullable=False)

    phone = Column(String(30), nullable=True)
    website = Column(String(500), nullable=True)

    whatsapp_phone_number_id = Column(String(200), nullable=True)
    whatsapp_business_account_id = Column(String(200), nullable=True)
    whatsapp_access_token = Column(String(1000), nullable=True)

    ai_enabled = Column(Boolean, default=True)
    active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
