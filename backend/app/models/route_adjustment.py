# backend/app/models/route_adjustment.py の修正
from sqlalchemy import Column, String, Integer, Float, JSON, Text, DateTime, Enum, ARRAY, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime

from app.models.database import Base


class AdjustmentType(str, enum.Enum):
    reorder = "reorder"  # 順序変更
    reassign = "reassign"  # 車両変更
    add_stop = "add_stop"  # 停止地点追加
    remove_stop = "remove_stop"  # 停止地点削除
    time_change = "time_change"  # 時間変更


class RouteAdjustment(Base):
    __tablename__ = "route_adjustments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id"))
    optimized_route_id = Column(UUID(as_uuid=True), ForeignKey("optimized_routes.id"))
    
    adjustment_type = Column(Enum(AdjustmentType))
    original_data = Column(JSON)  # 調整前
    adjusted_data = Column(JSON)  # 調整後
    reason = Column(Text)
    
    # 影響
    impact_distance_km = Column(Float)
    impact_time_minutes = Column(Integer)
    affected_guests = Column(ARRAY(UUID))
    
    # メタデータ
    adjusted_by = Column(String(100))
    adjusted_at = Column(DateTime, default=datetime.utcnow)
    applied = Column(Boolean, default=False)
    
    # リレーション
    tour = relationship("Tour")
    optimized_route = relationship("OptimizedRoute")