"""
ゲストモデル
"""

from sqlalchemy import Column, String, Integer, Float, Time, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.database import Base


class Guest(Base):
    __tablename__ = "guests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    hotel_name = Column(String(200))
    pickup_lat = Column(Float)
    pickup_lng = Column(Float)
    num_adults = Column(Integer, default=1)
    num_children = Column(Integer, default=0)
    preferred_pickup_start = Column(Time)
    preferred_pickup_end = Column(Time)
    phone = Column(String(20))
    email = Column(String(100))
    special_requirements = Column(ARRAY(Text), default=[])
    
    def to_dict(self):
        """辞書形式に変換"""
        return {
            "id": str(self.id),
            "name": self.name,
            "hotel_name": self.hotel_name,
            "pickup_lat": self.pickup_lat,
            "pickup_lng": self.pickup_lng,
            "num_adults": self.num_adults,
            "num_children": self.num_children,
            "preferred_pickup_start": self.preferred_pickup_start.isoformat() if self.preferred_pickup_start else None,
            "preferred_pickup_end": self.preferred_pickup_end.isoformat() if self.preferred_pickup_end else None,
            "phone": self.phone,
            "email": self.email,
            "special_requirements": self.special_requirements or []
        }