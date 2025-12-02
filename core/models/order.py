from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from datetime import datetime
from core.db import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)

    amount_cents = Column(Integer, nullable=False)
    commission_cents = Column(Integer, nullable=False)

    stripe_session_id = Column(String, unique=True, nullable=False)
    stripe_payment_intent_id = Column(String, nullable=True)
    status = Column(String, default="pending")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
