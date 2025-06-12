"""
ツアー参加者モデル（多対多の中間テーブル）
"""

from sqlalchemy import Column, Integer, Time, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.database import Base


class TourParticipant(Base):
    __tablename__ = "tour_participants"
    
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"), primary_key=True)
    guest_id = Column(UUID(as_uuid=True), ForeignKey("guests.id", ondelete="CASCADE"), primary_key=True)
    pickup_order = Column(Integer)
    actual_pickup_time = Column(Time)
    
    # リレーションシップ
    tour = relationship("Tour", back_populates="participants")
    guest = relationship("Guest", backref="tour_participations")
    
    def to_dict(self):
        """辞書形式に変換"""
        return {
            "tour_id": str(self.tour_id),
            "guest_id": str(self.guest_id),
            "pickup_order": self.pickup_order,
            "actual_pickup_time": self.actual_pickup_time.isoformat() if self.actual_pickup_time else None
        }