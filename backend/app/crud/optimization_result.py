"""
最適化結果のCRUD操作
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.models.optimized_route import OptimizedRoute
from app.models.tour import Tour, TourStatus
from app.schemas.optimization import OptimizationResult, VehicleRoute


class CRUDOptimizationResult:
    def save_result(
        self, 
        db: Session, 
        tour_id: UUID, 
        result: OptimizationResult
    ) -> List[OptimizedRoute]:
        """最適化結果をデータベースに保存"""
        # 既存の結果を削除
        db.query(OptimizedRoute).filter(
            OptimizedRoute.tour_id == tour_id
        ).delete()
        
        saved_routes = []
        for idx, route in enumerate(result.routes):
            # route_segmentsのtime型を文字列に変換
            segments_data = []
            for segment in route.route_segments:
                segment_dict = segment.dict()
                # timeオブジェクトを文字列に変換
                if 'arrival_time' in segment_dict and segment_dict['arrival_time']:
                    segment_dict['arrival_time'] = segment_dict['arrival_time'].strftime('%H:%M:%S')
                if 'departure_time' in segment_dict and segment_dict['departure_time']:
                    segment_dict['departure_time'] = segment_dict['departure_time'].strftime('%H:%M:%S')
                segments_data.append(segment_dict)
            
            # ルートデータを辞書形式で保存
            route_data = {
                "segments": segments_data,
                "assigned_guests": route.assigned_guests,
                "vehicle_utilization": route.vehicle_utilization,
                "vehicle_name": route.vehicle_name
            }
            
            db_route = OptimizedRoute(
                tour_id=tour_id,
                vehicle_id=UUID(route.vehicle_id),
                route_order=idx,
                total_distance_km=route.total_distance_km,
                total_time_minutes=route.total_duration_minutes,
                efficiency_score=route.efficiency_score,
                route_data=route_data
            )
            db.add(db_route)
            saved_routes.append(db_route)
        
        # ツアーステータスを更新
        tour = db.query(Tour).filter(Tour.id == tour_id).first()
        if tour:
            tour.status = TourStatus.confirmed
            tour.weather_data = {
                "fetched_at": datetime.now().isoformat(),
                "conditions": result.optimization_metrics.get("weather_conditions", "clear")
            }
        
        db.commit()
        return saved_routes
    
    def get_by_tour_id(
        self, 
        db: Session, 
        tour_id: UUID
    ) -> List[OptimizedRoute]:
        """ツアーIDで最適化結果を取得"""
        return db.query(OptimizedRoute).filter(
            OptimizedRoute.tour_id == tour_id
        ).order_by(OptimizedRoute.route_order).all()
    
    def delete_by_tour_id(
        self,
        db: Session,
        tour_id: UUID
    ) -> bool:
        """ツアーの最適化結果を削除"""
        db.query(OptimizedRoute).filter(
            OptimizedRoute.tour_id == tour_id
        ).delete()
        db.commit()
        return True


optimization_result = CRUDOptimizationResult()