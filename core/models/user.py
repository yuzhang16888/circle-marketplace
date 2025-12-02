from sqlalchemy import Column, Integer, String, Boolean
from core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Add Stripe columns
    stripe_account_id = Column(String, nullable=True)
    stripe_onboarded = Column(Boolean, default=False)
