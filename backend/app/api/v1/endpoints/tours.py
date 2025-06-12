"""
ツアー管理APIエンドポイント
"""

from typing import List, Optional
from datetime import date
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.tour import Tour, TourStatus
from app.schemas.tour import (
    TourCreate, TourUpdate, TourResponse, TourListResponse,
    TourParticipantInfo, OptimizedRouteInfo, TourOptimizeRequest
)
from app.crud.tour import tour as crud_tour
from app.crud.guest import guest as crud_guest
from app.api.v1.endpoints.optimize import run_optimization
from app.schemas.optimization import OptimizationRequest, Location

router = APIRouter()


def convert_tour_to_response(tour_obj) -> TourResponse:
    """ツアーオブジェクトをレスポンス形式に変換"""
    participants_info = []
    if hasattr(tour_obj, 'participants'):
        for tp in tour_obj.participants:
            if tp.guest:
                participants_info.append(TourParticipantInfo(
                    guest_id=tp.guest_id,
                    guest_name=tp.guest.name,
                    hotel_name=tp.guest.hotel_name,
                    pickup_order=tp.pickup_order,
                    actual_pickup_time=tp.actual_pickup_time
                ))
    
    routes_info = []
    if hasattr(tour_obj, 'optimized_routes'):
        for route in tour_obj.optimized_routes:
            routes_info.append(OptimizedRouteInfo(
                vehicle_id=route.vehicle_id,
                vehicle_name=route.vehicle.name if hasattr(route, 'vehicle') and route.vehicle else "Unknown",
                route_order=route.route_order,
                total_distance_km=float(route.total_distance_km) if route.total_distance_km else 0.0,
                total_time_minutes=route.total_time_minutes or 0,
                efficiency_score=float(route.efficiency_score) if route.efficiency_score else 0.0,
                route_data=route.route_data or {}
            ))
    
    # to_dict()の代わりに直接属性にアクセス
    tour_dict = {
        "id": tour_obj.id,
        "tour_date": tour_obj.tour_date,
        "activity_type": tour_obj.activity_type,
        "destination_name": tour_obj.destination_name,
        "destination_lat": tour_obj.destination_lat,
        "destination_lng": tour_obj.destination_lng,
        "departure_time": tour_obj.departure_time,
        "status": tour_obj.status,
        "optimization_strategy": tour_obj.optimization_strategy,
        "weather_data": tour_obj.weather_data,
        "created_at": getattr(tour_obj, 'created_at', None),
        "updated_at": getattr(tour_obj, 'updated_at', None)
    }
    
    return TourResponse(
        **tour_dict,
        participants=participants_info,
        optimized_routes=routes_info,
        total_participants=len(participants_info),
        total_vehicles_used=len(routes_info)
    )


@router.get("/", response_model=TourListResponse)
def read_tours(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tour_date: Optional[date] = Query(None, description="特定の日付でフィルタ"),
    status: Optional[TourStatus] = Query(None, description="ツアーステータスでフィルタ"),
    db: Session = Depends(get_db)
):
    """
    ツアー一覧を取得
    
    - **skip**: スキップする件数
    - **limit**: 取得する最大件数
    - **tour_date**: 特定の日付でフィルタ
    - **status**: ツアーステータス
    """
    tours = crud_tour.get_multi(
        db, skip=skip, limit=limit, 
        tour_date=tour_date, status=status
    )
    
    # totalの計算を修正
    query = db.query(Tour)
    if tour_date:
        query = query.filter(Tour.tour_date == tour_date)
    if status:
        query = query.filter(Tour.status == status)
    total = query.count()
    
    return TourListResponse(
        tours=[convert_tour_to_response(t) for t in tours],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("/", response_model=TourResponse)
def create_tour(
    tour_in: TourCreate,
    db: Session = Depends(get_db)
):
    """
    新しいツアーを作成
    
    参加者IDのリストを指定してツアーを作成します。
    """
    # 参加者の存在確認
    for guest_id in tour_in.participant_ids:
        guest = crud_guest.get(db, guest_id)
        if not guest:
            raise HTTPException(
                status_code=400,
                detail=f"Guest {guest_id} not found"
            )
    
    tour = crud_tour.create(
        db=db, 
        obj_in=tour_in,
        participant_ids=tour_in.participant_ids
    )
    
    return convert_tour_to_response(tour)


@router.get("/upcoming", response_model=List[TourResponse])
def read_upcoming_tours(
    days: int = Query(7, ge=1, le=30, description="今後何日分のツアーを取得するか"),
    db: Session = Depends(get_db)
):
    """
    今後のツアーを取得
    """
    tours = crud_tour.get_upcoming_tours(db, days=days)
    return [convert_tour_to_response(t) for t in tours]


@router.get("/{tour_id}", response_model=TourResponse)
def read_tour(
    tour_id: UUID,
    db: Session = Depends(get_db)
):
    """
    特定のツアー情報を取得
    """
    tour = crud_tour.get(db=db, tour_id=tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    return convert_tour_to_response(tour)


@router.put("/{tour_id}", response_model=TourResponse)
def update_tour(
    tour_id: UUID,
    tour_in: TourUpdate,
    db: Session = Depends(get_db)
):
    """
    ツアー情報を更新
    """
    tour = crud_tour.get(db=db, tour_id=tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    tour = crud_tour.update(db=db, db_obj=tour, obj_in=tour_in)
    return convert_tour_to_response(tour)


@router.delete("/{tour_id}", response_model=TourResponse)
def delete_tour(
    tour_id: UUID,
    db: Session = Depends(get_db)
):
    """
    ツアーを削除
    """
    tour = crud_tour.get(db=db, tour_id=tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    deleted_tour = crud_tour.delete(db=db, tour_id=tour_id)
    return convert_tour_to_response(deleted_tour)


@router.post("/{tour_id}/participants/{guest_id}", response_model=TourResponse)
def add_participant(
    tour_id: UUID,
    guest_id: UUID,
    db: Session = Depends(get_db)
):
    """
    ツアーに参加者を追加
    """
    tour = crud_tour.get(db=db, tour_id=tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    guest = crud_guest.get(db=db, guest_id=guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    tour = crud_tour.add_participant(db=db, tour_id=tour_id, guest_id=guest_id)
    return convert_tour_to_response(tour)


@router.delete("/{tour_id}/participants/{guest_id}", response_model=TourResponse)
def remove_participant(
    tour_id: UUID,
    guest_id: UUID,
    db: Session = Depends(get_db)
):
    """
    ツアーから参加者を削除
    """
    tour = crud_tour.remove_participant(db=db, tour_id=tour_id, guest_id=guest_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tour or participant not found")
    
    return convert_tour_to_response(tour)


@router.post("/{tour_id}/optimize", response_model=dict)
async def optimize_tour(
    tour_id: UUID,
    request: Optional[TourOptimizeRequest] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    ツアーの最適化を実行
    
    データベースに保存されているツアー情報を使用して、
    ルート最適化を実行します。
    """
    tour = crud_tour.get(db=db, tour_id=tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    # 最適化リクエストを構築
    participant_ids = [str(p.guest_id) for p in tour.participants]
    
    optimization_request = OptimizationRequest(
        tour_date=tour.tour_date,
        activity_type=tour.activity_type.value,
        destination=Location(
            name=tour.destination_name,
            lat=tour.destination_lat,
            lng=tour.destination_lng
        ),
        participant_ids=participant_ids,
        available_vehicle_ids=[],  # 自動選択
        optimization_strategy=tour.optimization_strategy,
        departure_time=tour.departure_time
    )
    
    # 最適化ジョブを開始
    job_id = f"tour_{tour_id}_{uuid4().hex[:8]}"
    
    # バックグラウンドで実行
    background_tasks.add_task(
        run_optimization,
        job_id=job_id,
        request=optimization_request
    )
    
    return {
        "job_id": job_id,
        "tour_id": str(tour_id),
        "message": "Optimization started"
    }