"""
ツアーモデル
"""

from sqlalchemy import Column, String, Float, Date, Time, Enum, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime

from app.models.database import Base


class ActivityType(str, enum.Enum):
    snorkeling = "snorkeling"
    diving = "diving"
    sightseeing = "sightseeing"
    kayaking = "kayaking"
    fishing = "fishing"


class TourStatus(str, enum.Enum):
    planning = "planning"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class Tour(Base):
    __tablename__ = "tours"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_date = Column(Date, nullable=False)
    activity_type = Column(Enum(ActivityType), nullable=False)
    destination_name = Column(String(200))
    destination_lat = Column(Float)
    destination_lng = Column(Float)
    departure_time = Column(Time, nullable=False)
    status = Column(Enum(TourStatus), default=TourStatus.planning)
    optimization_strategy = Column(String(20), default="balanced")
    weather_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    participants = relationship("TourParticipant", back_populates="tour", cascade="all, delete-orphan")
    optimized_routes = relationship("OptimizedRoute", back_populates="tour", cascade="all, delete-orphan")
    
    def to_dict(self):
        """辞書形式に変換"""
        return {
            "id": str(self.id),
            "tour_date": self.tour_date.isoformat() if self.tour_date else None,
            "activity_type": self.activity_type.value if self.activity_type else None,
            "destination_name": self.destination_name,
            "destination_lat": self.destination_lat,
            "destination_lng": self.destination_lng,
            "departure_time": self.departure_time.isoformat() if self.departure_time else None,
            "status": self.status.value if self.status else None,
            "optimization_strategy": self.optimization_strategy,
            "weather_data": self.weather_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }