from typing import List, Optional, Literal, Dict, Any
from datetime import date, time, datetime
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class Location(BaseModel):
    """位置情報"""
    name: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class TimeWindow(BaseModel):
    """時間窓（希望ピックアップ時間帯）"""
    start: time
    end: time
    
    @validator('end')
    def end_after_start(cls, v, values):
        if 'start' in values and v <= values['start']:
            raise ValueError('終了時刻は開始時刻より後である必要があります')
        return v


class Guest(BaseModel):
    """ゲスト情報"""
    id: str
    name: str
    hotel_name: str
    pickup_location: Location
    num_adults: int = Field(1, ge=1)
    num_children: int = Field(0, ge=0)
    preferred_time_window: Optional[TimeWindow] = None
    special_requirements: List[str] = []
    
    @property
    def total_passengers(self) -> int:
        return self.num_adults + self.num_children


class Vehicle(BaseModel):
    """車両情報"""
    id: str
    name: str
    capacity_adults: int = Field(..., ge=1)
    capacity_children: int = Field(..., ge=0)
    driver_name: str
    current_location: Optional[Location] = None
    vehicle_type: Literal["sedan", "van", "minibus"] = "van"
    equipment: List[str] = []  # ["child_seat", "wheelchair_accessible", etc.]
    
    @property
    def total_capacity(self) -> int:
        return self.capacity_adults + self.capacity_children


class OptimizationConstraints(BaseModel):
    """最適化制約条件"""
    max_pickup_time_minutes: int = Field(90, ge=30, le=180)
    buffer_time_minutes: int = Field(15, ge=5, le=30)
    weather_consideration: bool = True
    max_distance_km: Optional[float] = None
    priority_hotels: List[str] = []  # 優先的にピックアップするホテル


class OptimizationRequest(BaseModel):
    """最適化リクエスト"""
    tour_id: Optional[str] = None  # tour_idを追加（オプショナル）
    tour_date: date
    activity_type: Literal["snorkeling", "diving", "sightseeing", "kayaking", "fishing"]
    destination: Location
    participant_ids: List[str] = Field(..., min_items=1)
    available_vehicle_ids: List[str] = Field(..., min_items=1)
    constraints: OptimizationConstraints = OptimizationConstraints()
    optimization_strategy: Literal["safety", "efficiency", "balanced"] = "balanced"
    departure_time: time = time(8, 0)  # ツアー出発希望時刻


class RouteSegment(BaseModel):
    """ルートの1区間"""
    from_location: Location
    to_location: Location
    guest_id: Optional[str] = None
    distance_km: float
    duration_minutes: int
    arrival_time: time
    departure_time: time


class VehicleRoute(BaseModel):
    """車両ごとのルート"""
    vehicle_id: str
    vehicle_name: str
    route_segments: List[RouteSegment]
    assigned_guests: List[str]
    total_distance_km: float
    total_duration_minutes: int
    efficiency_score: float = Field(..., ge=0, le=1)
    vehicle_utilization: float = Field(..., ge=0, le=1)  # 車両容量の使用率


class OptimizationResult(BaseModel):
    """最適化結果"""
    tour_id: str
    status: Literal["success", "partial", "failed"]
    total_vehicles_used: int
    routes: List[VehicleRoute]
    total_distance_km: float
    total_time_minutes: int
    average_efficiency_score: float
    optimization_metrics: Dict[str, Any]
    warnings: List[str] = []
    computation_time_seconds: float


class OptimizationJobStatus(BaseModel):
    """最適化ジョブの状態"""
    job_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    created_at: datetime
    updated_at: datetime
    estimated_completion_seconds: Optional[int] = None
    progress_percentage: int = Field(0, ge=0, le=100)
    result: Optional[OptimizationResult] = None
    error_message: Optional[str] = None