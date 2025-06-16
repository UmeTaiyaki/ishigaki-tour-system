"""
最適化結果モデル
"""

from sqlalchemy import Column, Integer, Float, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.models.database import Base


class OptimizedRoute(Base):
    __tablename__ = "optimized_routes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"))
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"))
    route_order = Column(Integer)
    total_distance_km = Column(Float)
    total_time_minutes = Column(Integer)
    efficiency_score = Column(Float)
    route_data = Column(JSON)  # 詳細なルート情報
    created_at = Column(DateTime, default=datetime.utcnow)  # created_atを追加
    
    # リレーションシップ
    tour = relationship("Tour", back_populates="optimized_routes")
    vehicle = relationship("Vehicle")
    
    def to_dict(self):
        """辞書形式に変換"""
        return {
            "id": str(self.id),
            "tour_id": str(self.tour_id),
            "vehicle_id": str(self.vehicle_id),
            "route_order": self.route_order,
            "total_distance_km": self.total_distance_km,
            "total_time_minutes": self.total_time_minutes,
            "efficiency_score": self.efficiency_score,
            "route_data": self.route_data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }