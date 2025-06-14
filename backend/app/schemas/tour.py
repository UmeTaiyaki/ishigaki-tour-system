"""
ツアー関連のスキーマ定義
"""

from typing import List, Optional, Dict, Any
from datetime import date, time, datetime
from pydantic import BaseModel, Field
from uuid import UUID

from app.models.tour import ActivityType, TourStatus


class TourBase(BaseModel):
    """ツアーの基本情報"""
    tour_date: date
    activity_type: ActivityType
    destination_name: str = Field(..., max_length=200)
    destination_lat: float = Field(..., ge=-90, le=90)
    destination_lng: float = Field(..., ge=-180, le=180)
    departure_time: time
    status: TourStatus = TourStatus.planning
    optimization_strategy: str = Field("balanced", max_length=20)
    weather_data: Optional[Dict[str, Any]] = None


class TourCreate(TourBase):
    """ツアー作成用スキーマ"""
    participant_ids: List[UUID] = Field(..., min_items=1)
    vehicle_ids: Optional[List[UUID]] = None  # 指定しない場合は自動選択


class TourUpdate(BaseModel):
    """ツアー更新用スキーマ"""
    tour_date: Optional[date] = None
    activity_type: Optional[ActivityType] = None
    destination_name: Optional[str] = Field(None, max_length=200)
    destination_lat: Optional[float] = Field(None, ge=-90, le=90)
    destination_lng: Optional[float] = Field(None, ge=-180, le=180)
    departure_time: Optional[time] = None
    status: Optional[TourStatus] = None
    optimization_strategy: Optional[str] = Field(None, max_length=20)
    weather_data: Optional[Dict[str, Any]] = None


class TourParticipantInfo(BaseModel):
    """ツアー参加者情報"""
    guest_id: UUID
    guest_name: str
    hotel_name: Optional[str]
    pickup_order: Optional[int]
    actual_pickup_time: Optional[time]


class OptimizedRouteInfo(BaseModel):
    """最適化されたルート情報"""
    vehicle_id: UUID
    vehicle_name: str
    route_order: int
    total_distance_km: float
    total_time_minutes: int
    efficiency_score: float
    route_data: Dict[str, Any]


class TourInDB(TourBase):
    """データベースから取得したツアー情報"""
    id: UUID
    created_at: Optional[datetime] = None  # Optionalに変更
    updated_at: Optional[datetime] = None  # Optionalに変更
    
    class Config:
        from_attributes = True


class TourResponse(TourInDB):
    """APIレスポンス用のツアー情報"""
    participants: List[TourParticipantInfo] = []
    optimized_routes: List[OptimizedRouteInfo] = []
    total_participants: int = 0
    total_vehicles_used: int = 0


class TourListResponse(BaseModel):
    """ツアー一覧レスポンス"""
    tours: List[TourResponse]
    total: int
    skip: int
    limit: int


class TourOptimizeRequest(BaseModel):
    """ツアー最適化リクエスト"""
    tour_id: UUID
    constraints: Optional[Dict[str, Any]] = None
    force_recalculate: bool = False