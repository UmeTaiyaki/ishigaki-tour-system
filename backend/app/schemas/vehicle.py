"""
車両関連のスキーマ定義
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID

from app.models.vehicle import VehicleType, VehicleStatus


class VehicleBase(BaseModel):
    """車両の基本情報"""
    name: str = Field(..., min_length=1, max_length=100)
    capacity_adults: int = Field(..., ge=1)
    capacity_children: int = Field(..., ge=0)
    driver_name: Optional[str] = Field(None, max_length=100)
    driver_phone: Optional[str] = Field(None, max_length=20)
    current_lat: Optional[float] = Field(None, ge=-90, le=90)
    current_lng: Optional[float] = Field(None, ge=-180, le=180)
    vehicle_type: Optional[VehicleType] = VehicleType.van
    fuel_type: Optional[str] = Field(None, max_length=20)
    license_plate: Optional[str] = Field(None, max_length=20)
    status: VehicleStatus = VehicleStatus.available
    equipment: List[str] = []


class VehicleCreate(VehicleBase):
    """車両作成用スキーマ"""
    pass


class VehicleUpdate(BaseModel):
    """車両更新用スキーマ（部分更新可能）"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    capacity_adults: Optional[int] = Field(None, ge=1)
    capacity_children: Optional[int] = Field(None, ge=0)
    driver_name: Optional[str] = Field(None, max_length=100)
    driver_phone: Optional[str] = Field(None, max_length=20)
    current_lat: Optional[float] = Field(None, ge=-90, le=90)
    current_lng: Optional[float] = Field(None, ge=-180, le=180)
    vehicle_type: Optional[VehicleType] = None
    fuel_type: Optional[str] = Field(None, max_length=20)
    license_plate: Optional[str] = Field(None, max_length=20)
    status: Optional[VehicleStatus] = None
    equipment: Optional[List[str]] = None


class VehicleInDB(VehicleBase):
    """データベースから取得した車両情報"""
    id: UUID
    
    class Config:
        from_attributes = True


class VehicleResponse(VehicleInDB):
    """APIレスポンス用の車両情報"""
    pass