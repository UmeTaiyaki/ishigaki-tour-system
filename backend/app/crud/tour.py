"""
ツアーのCRUD操作
"""

from typing import List, Optional
from datetime import date, datetime
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.models.tour import Tour, TourStatus
from app.models.tour_participant import TourParticipant
from app.models.guest import Guest
from app.schemas.tour import TourCreate, TourUpdate


class CRUDTour:
    def __init__(self):
        self.model = Tour  # モデルクラスを指定
    
    def get(self, db: Session, tour_id: UUID) -> Optional[Tour]:
        """IDでツアーを取得（関連データも含む）"""
        return db.query(Tour).options(
            joinedload(Tour.participants).joinedload(TourParticipant.guest),
            joinedload(Tour.optimized_routes)
        ).filter(Tour.id == tour_id).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        tour_date: Optional[date] = None,
        status: Optional[TourStatus] = None
    ) -> List[Tour]:
        """ツアー一覧を取得"""
        query = db.query(Tour).options(
            joinedload(Tour.participants).joinedload(TourParticipant.guest),
            joinedload(Tour.optimized_routes)
        )
        
        if tour_date:
            query = query.filter(Tour.tour_date == tour_date)
        
        if status:
            query = query.filter(Tour.status == status)
        
        return query.order_by(Tour.tour_date.desc()).offset(skip).limit(limit).all()
    
    def create(self, db: Session, obj_in: TourCreate, participant_ids: List[UUID]) -> Tour:
        """ツアーを作成"""
        # ツアー本体を作成
        tour_data = obj_in.model_dump(exclude={'participant_ids', 'vehicle_ids'})
        db_tour = Tour(**tour_data)
        db.add(db_tour)
        db.flush()  # IDを生成
        
        # 参加者を追加
        for idx, guest_id in enumerate(participant_ids):
            participant = TourParticipant(
                tour_id=db_tour.id,
                guest_id=guest_id,
                pickup_order=idx + 1  # 仮の順番
            )
            db.add(participant)
        
        db.commit()
        db.refresh(db_tour)
        return self.get(db, db_tour.id)
    
    def update(
        self, 
        db: Session, 
        db_obj: Tour, 
        obj_in: TourUpdate
    ) -> Tour:
        """ツアー情報を更新"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db_obj.updated_at = datetime.now()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return self.get(db, db_obj.id)
    
    def delete(self, db: Session, tour_id: UUID) -> Tour:
        """ツアーを削除（関連データも削除される）"""
        tour = self.get(db, tour_id)
        if tour:
            db.delete(tour)
            db.commit()
        return tour
    
    def add_participant(
        self, 
        db: Session, 
        tour_id: UUID, 
        guest_id: UUID
    ) -> Optional[Tour]:
        """ツアーに参加者を追加"""
        # 既に参加しているかチェック
        existing = db.query(TourParticipant).filter(
            and_(
                TourParticipant.tour_id == tour_id,
                TourParticipant.guest_id == guest_id
            )
        ).first()
        
        if not existing:
            # 最大のpickup_orderを取得
            max_order = db.query(TourParticipant).filter(
                TourParticipant.tour_id == tour_id
            ).count()
            
            participant = TourParticipant(
                tour_id=tour_id,
                guest_id=guest_id,
                pickup_order=max_order + 1
            )
            db.add(participant)
            db.commit()
        
        return self.get(db, tour_id)
    
    def remove_participant(
        self, 
        db: Session, 
        tour_id: UUID, 
        guest_id: UUID
    ) -> Optional[Tour]:
        """ツアーから参加者を削除"""
        participant = db.query(TourParticipant).filter(
            and_(
                TourParticipant.tour_id == tour_id,
                TourParticipant.guest_id == guest_id
            )
        ).first()
        
        if participant:
            db.delete(participant)
            db.commit()
        
        return self.get(db, tour_id)
    
    def get_by_date_range(
        self,
        db: Session,
        start_date: date,
        end_date: date
    ) -> List[Tour]:
        """日付範囲でツアーを検索"""
        return db.query(Tour).filter(
            and_(
                Tour.tour_date >= start_date,
                Tour.tour_date <= end_date
            )
        ).order_by(Tour.tour_date).all()
    
    def get_upcoming_tours(
        self,
        db: Session,
        days: int = 7
    ) -> List[Tour]:
        """今後のツアーを取得"""
        from datetime import date, timedelta
        today = date.today()
        end_date = today + timedelta(days=days)
        
        return self.get_by_date_range(db, today, end_date)


tour = CRUDTour()