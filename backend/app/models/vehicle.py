"""
車両モデル
"""

from sqlalchemy import Column, String, Integer, Float, Enum, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from app.models.database import Base


class VehicleType(str, enum.Enum):
    sedan = "sedan"
    van = "van"
    minibus = "minibus"


class VehicleStatus(str, enum.Enum):
    available = "available"
    in_use = "in_use"
    maintenance = "maintenance"


class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    capacity_adults = Column(Integer, nullable=False)
    capacity_children = Column(Integer, nullable=False)
    driver_name = Column(String(100))
    driver_phone = Column(String(20))
    current_lat = Column(Float)
    current_lng = Column(Float)
    vehicle_type = Column(Enum(VehicleType))
    fuel_type = Column(String(20))
    license_plate = Column(String(20))
    status = Column(Enum(VehicleStatus), default=VehicleStatus.available)
    equipment = Column(ARRAY(Text), default=[])
    
    def to_dict(self):
        """辞書形式に変換"""
        return {
            "id": str(self.id),
            "name": self.name,
            "capacity_adults": self.capacity_adults,
            "capacity_children": self.capacity_children,
            "driver_name": self.driver_name,
            "driver_phone": self.driver_phone,
            "current_lat": self.current_lat,
            "current_lng": self.current_lng,
            "vehicle_type": self.vehicle_type.value if self.vehicle_type else None,
            "fuel_type": self.fuel_type,
            "license_plate": self.license_plate,
            "status": self.status.value if self.status else None,
            "equipment": self.equipment or []
        }