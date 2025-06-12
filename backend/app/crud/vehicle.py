"""
車両のCRUD操作
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


class CRUDVehicle:
    def get(self, db: Session, vehicle_id: UUID) -> Optional[Vehicle]:
        """IDで車両を取得"""
        return db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[VehicleStatus] = None
    ) -> List[Vehicle]:
        """車両一覧を取得"""
        query = db.query(Vehicle)
        
        if status:
            query = query.filter(Vehicle.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, obj_in: VehicleCreate) -> Vehicle:
        """車両を作成"""
        db_obj = Vehicle(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        db_obj: Vehicle, 
        obj_in: VehicleUpdate
    ) -> Vehicle:
        """車両情報を更新"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, vehicle_id: UUID) -> Vehicle:
        """車両を削除"""
        obj = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        db.delete(obj)
        db.commit()
        return obj
    
    def get_available(self, db: Session) -> List[Vehicle]:
        """利用可能な車両を取得"""
        return db.query(Vehicle).filter(
            Vehicle.status == VehicleStatus.available
        ).all()
    
    def get_by_capacity(
        self, 
        db: Session, 
        min_adults: int,
        min_children: int = 0
    ) -> List[Vehicle]:
        """必要な容量を満たす車両を取得"""
        return db.query(Vehicle).filter(
            Vehicle.capacity_adults >= min_adults,
            Vehicle.capacity_children >= min_children,
            Vehicle.status == VehicleStatus.available
        ).all()


vehicle = CRUDVehicle()