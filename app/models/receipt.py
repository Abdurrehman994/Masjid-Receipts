from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime
import enum


class PaymentMode(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    CHEQUE = "cheque"
    OTHER = "other"


receipt_tags = Table(
    'receipt_tags',
    Base.metadata,
    Column('receipt_id', Integer, ForeignKey('receipts.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    payment_mode = Column(Enum(PaymentMode), nullable=False)
    note = Column(String, nullable=True)
    image_path = Column(String, nullable=True)
    store_name = Column(String, nullable=True)
    receipt_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    uploader = relationship("User", back_populates="receipts")
    tags = relationship("Tag", secondary=receipt_tags, back_populates="receipts")
