from pydantic import BaseModel
from datetime import datetime
from app.models.receipt import PaymentMode
from app.schemas.tag import Tag
from typing import List, Optional


class ReceiptBase(BaseModel):
    """Base receipt fields"""
    amount: float
    category: str
    payment_mode: PaymentMode
    note: Optional[str] = None
    store_name: Optional[str] = None
    receipt_date: Optional[datetime] = None


class ReceiptCreate(ReceiptBase):
    """Schema for creating a receipt"""
    pass


class Receipt(ReceiptBase):
    """Schema for receipt response"""
    id: int
    image_path: Optional[str] = None
    uploaded_by: int
    created_at: datetime
    tags: List[Tag] = []

    class Config:
        from_attributes = True


class ReceiptWithUploader(Receipt):
    """Extended receipt with uploader name"""
    uploader_name: str


class ReceiptUpdate(BaseModel):
    """Schema for updating a receipt: all fields optional"""
    amount: Optional[float] = None
    category: Optional[str] = None
    payment_mode: Optional[PaymentMode] = None
    note: Optional[str] = None
    store_name: Optional[str] = None
    receipt_date: Optional[datetime] = None
    image_path: Optional[str] = None
    tags: Optional[List[Tag]] = None