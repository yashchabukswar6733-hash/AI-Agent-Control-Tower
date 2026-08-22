from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime

from backend.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)

    business_id = Column(
        Integer,
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )

    customer_phone = Column(String(40), nullable=False, index=True)
    customer_name = Column(String(200), nullable=True)

    direction = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)

    ai_generated = Column(String(10), default="false")
    status = Column(String(30), default="open")

    created_at = Column(DateTime, default=datetime.utcnow)
