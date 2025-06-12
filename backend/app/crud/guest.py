"""
ゲストのCRUD操作
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.guest import Guest
from app.schemas.guest import GuestCreate, GuestUpdate


class CRUDGuest:
    def get(self, db: Session, guest_id: UUID) -> Optional[Guest]:
        """IDでゲストを取得"""
        return db.query(Guest).filter(Guest.id == guest_id).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Guest]:
        """ゲスト一覧を取得"""
        query = db.query(Guest)
        
        if search:
            search_filter = or_(
                Guest.name.ilike(f"%{search}%"),
                Guest.hotel_name.ilike(f"%{search}%"),
                Guest.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, obj_in: GuestCreate) -> Guest:
        """ゲストを作成"""
        db_obj = Guest(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        db_obj: Guest, 
        obj_in: GuestUpdate
    ) -> Guest:
        """ゲスト情報を更新"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, guest_id: UUID) -> Guest:
        """ゲストを削除"""
        obj = db.query(Guest).filter(Guest.id == guest_id).first()
        db.delete(obj)
        db.commit()
        return obj
    
    def get_by_hotel(self, db: Session, hotel_name: str) -> List[Guest]:
        """ホテル名でゲストを検索"""
        return db.query(Guest).filter(
            Guest.hotel_name.ilike(f"%{hotel_name}%")
        ).all()


guest = CRUDGuest()