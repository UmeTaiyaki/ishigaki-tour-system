# backend/app/schemas/optimization.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal, Union
from datetime import date, time, datetime
from uuid import UUID


class Location(BaseModel):
    """位置情報"""
    name: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class TimeWindow(BaseModel):
    """時間窓"""
    start_time: Union[time, str] = Field(alias='start')
    end_time: Union[time, str] = Field(alias='end')
    
    class Config:
        populate_by_name = True  # Pydantic v2形式に更新
        json_encoders = {
            time: lambda v: v.strftime("%H:%M:%S") if v else None
        }
    
    @validator('start_time', 'end_time', pre=True)
    def parse_time(cls, v):
        """時刻の柔軟な解析"""
        if isinstance(v, time):
            return v
        elif isinstance(v, str):
            # HH:MM:SS 形式
            try:
                return datetime.strptime(v, "%H:%M:%S").time()
            except ValueError:
                pass
            # HH:MM 形式
            try:
                return datetime.strptime(v, "%H:%M").time()
            except ValueError:
                pass
            raise ValueError(f"Invalid time format: {v}")
        elif isinstance(v, dict):
            # 辞書形式の場合
            if 'datetime.time' in str(v):
                import re
                match = re.search(r'datetime\.time\((\d+),\s*(\d+)(?:,\s*(\d+))?\)', str(v))
                if match:
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    second = int(match.group(3)) if match.group(3) else 0
                    return time(hour, minute, second)
            raise ValueError(f"Cannot parse time from dict: {v}")
        else:
            raise ValueError(f"Invalid time type: {type(v)}")


class Guest(BaseModel):
    """ゲスト情報"""
    id: str
    name: str
    hotel_name: str
    pickup_location: Location
    num_adults: int = Field(..., ge=1)
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
    driver_name: Optional[str] = None
    vehicle_type: Literal["sedan", "van", "minibus"] = "van"
    equipment: List[str] = []
    
    @property
    def total_capacity(self) -> int:
        return self.capacity_adults + self.capacity_children


class OptimizationConstraints(BaseModel):
    """最適化制約条件"""
    max_pickup_time_minutes: int = Field(90, ge=30, le=180)
    buffer_time_minutes: int = Field(15, ge=5, le=30)
    weather_consideration: bool = True
    max_distance_km: Optional[float] = None
    priority_hotels: List[str] = []
    priority_time_window: Optional[TimeWindow] = None
    incompatible_pairs: Optional[List[List[str]]] = None


class OptimizationRequest(BaseModel):
    """最適化リクエスト"""
    tour_id: Optional[str] = None
    tour_date: date
    activity_type: Literal["snorkeling", "diving", "sightseeing", "kayaking", "fishing"]
    destination: Location
    participant_ids: List[str] = Field(..., min_items=1)
    available_vehicle_ids: List[str] = Field(..., min_items=1)
    constraints: OptimizationConstraints = OptimizationConstraints()
    optimization_strategy: Literal["safety", "efficiency", "balanced"] = "balanced"
    departure_time: time = time(8, 0)
    weather_conditions: Optional[Dict[str, Any]] = None


class RouteSegment(BaseModel):
    """ルートの1区間"""
    from_location: Location
    to_location: Location
    guest_id: Optional[str] = None
    distance_km: float
    duration_minutes: int
    arrival_time: time
    departure_time: time
    
    class Config:
        json_encoders = {
            time: lambda v: v.strftime("%H:%M:%S") if v else None
        }


class VehicleRoute(BaseModel):
    """車両ごとのルート"""
    vehicle_id: str
    vehicle_name: str
    route_segments: List[RouteSegment]
    assigned_guests: List[str]
    total_distance_km: float
    total_duration_minutes: int
    efficiency_score: float = Field(..., ge=0, le=1)
    vehicle_utilization: float = Field(..., ge=0, le=1)


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
    current_step: Optional[str] = None  # Optionalに変更
    result: Optional[OptimizationResult] = None
    error_message: Optional[str] = None