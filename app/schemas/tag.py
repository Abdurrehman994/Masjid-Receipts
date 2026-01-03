from pydantic import BaseModel
from typing import Optional


class TagBase(BaseModel):
    """Base tag fields"""
    name: str
    description: Optional[str] = None


class TagCreate(TagBase):
    """Schema for creating a tag"""
    pass


class Tag(TagBase):
    """Schema for tag response"""
    id: int

    class Config:
        from_attributes = True


class TagWithCount(Tag):
    """Tag with receipt count"""
    receipt_count: int