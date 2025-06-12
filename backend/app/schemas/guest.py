"""
ゲスト関連のスキーマ定義
"""

from typing import List, Optional
from datetime import time
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class GuestBase(BaseModel):
    """ゲストの基本情報"""
    name: str = Field(..., min_length=1, max_length=100)
    hotel_name: Optional[str] = Field(None, max_length=200)
    pickup_lat: Optional[float] = Field(None, ge=-90, le=90)
    pickup_lng: Optional[float] = Field(None, ge=-180, le=180)
    num_adults: int = Field(1, ge=1)
    num_children: int = Field(0, ge=0)
    preferred_pickup_start: Optional[time] = None
    preferred_pickup_end: Optional[time] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    special_requirements: List[str] = []


class GuestCreate(GuestBase):
    """ゲスト作成用スキーマ"""
    pass


class GuestUpdate(BaseModel):
    """ゲスト更新用スキーマ（部分更新可能）"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    hotel_name: Optional[str] = Field(None, max_length=200)
    pickup_lat: Optional[float] = Field(None, ge=-90, le=90)
    pickup_lng: Optional[float] = Field(None, ge=-180, le=180)
    num_adults: Optional[int] = Field(None, ge=1)
    num_children: Optional[int] = Field(None, ge=0)
    preferred_pickup_start: Optional[time] = None
    preferred_pickup_end: Optional[time] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    special_requirements: Optional[List[str]] = None


class GuestInDB(GuestBase):
    """データベースから取得したゲスト情報"""
    id: UUID
    
    class Config:
        from_attributes = True


class GuestResponse(GuestInDB):
    """APIレスポンス用のゲスト情報"""
    pass