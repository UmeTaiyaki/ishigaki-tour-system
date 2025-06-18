# backend/app/api/v1/endpoints/optimize.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, List
import uuid
from uuid import UUID
from datetime import datetime, time
import logging
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.schemas.optimization import (
    OptimizationRequest,
    OptimizationResult,
    OptimizationJobStatus,
    Guest,
    Vehicle,
    Location,
    TimeWindow,
    VehicleRoute,
    RouteSegment
)
from app.crud.optimization_result import optimization_result as crud_optimization_result

logger = logging.getLogger(__name__)

# ルーターを作成
router = APIRouter()

# 一時的なメモリストレージ（後でRedisやDBに置き換え）
optimization_jobs: Dict[str, OptimizationJobStatus] = {}

# 最適化エンジンのインスタンス（遅延インポート）
optimizer = None


def get_optimizer():
    """最適化エンジンを遅延初期化"""
    global optimizer
    if optimizer is None:
        try:
            from app.optimizer.route_optimizer import RouteOptimizer
            optimizer = RouteOptimizer()
            logger.info("Route optimizer initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to import RouteOptimizer: {e}")
    return optimizer


@router.post("/route", response_model=OptimizationJobStatus)
async def optimize_route(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    ツアールートの最適化を開始する
    
    - 非同期処理として最適化を実行
    - ジョブIDを返却し、後でステータス確認可能
    """
    job_id = f"opt_job_{uuid.uuid4().hex[:8]}"
    
    # ジョブステータス初期化
    job_status = OptimizationJobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        estimated_completion_seconds=10,
        progress_percentage=0,
        current_step="初期化中"
    )
    
    optimization_jobs[job_id] = job_status
    
    # バックグラウンドで最適化実行
    background_tasks.add_task(
        run_optimization,
        job_id=job_id,
        request=request,
        db=db
    )
    
    logger.info(f"Optimization job started: {job_id}")
    return job_status


@router.get("/status/{job_id}", response_model=OptimizationJobStatus)
async def get_optimization_status(job_id: str):
    """最適化ジョブのステータスを取得"""
    if job_id not in optimization_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return optimization_jobs[job_id]


@router.get("/result/{job_id}", response_model=OptimizationResult)
async def get_optimization_result(job_id: str):
    """最適化結果を取得"""
    if job_id not in optimization_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_status = optimization_jobs[job_id]
    
    if job_status.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is {job_status.status}. Results not available yet."
        )
    
    if not job_status.result:
        raise HTTPException(status_code=500, detail="Result not found")
    
    return job_status.result


def run_optimization(job_id: str, request: OptimizationRequest, db: Session):
    """
    最適化を実行する（DBセッション付き）
    """
    try:
        # ステータス更新
        optimization_jobs[job_id].status = "processing"
        optimization_jobs[job_id].updated_at = datetime.now()
        optimization_jobs[job_id].progress_percentage = 10
        optimization_jobs[job_id].current_step = "データ準備中"
        
        # DBからゲストと車両データを取得
        from app.crud.guest import guest as crud_guest
        from app.crud.vehicle import vehicle as crud_vehicle
        
        # ゲスト情報を取得
        guests = []
        for guest_id in request.participant_ids:
            db_guest = crud_guest.get(db, UUID(guest_id))
            if db_guest:
                guest = Guest(
                    id=str(db_guest.id),
                    name=db_guest.name,
                    hotel_name=db_guest.hotel_name or "不明",
                    pickup_location=Location(
                        name=db_guest.hotel_name or "ピックアップ地点",
                        lat=db_guest.pickup_lat or 24.3448,
                        lng=db_guest.pickup_lng or 124.1572
                    ),
                    num_adults=db_guest.num_adults,
                    num_children=db_guest.num_children,
                    preferred_time_window=TimeWindow(
                        start_time=db_guest.preferred_pickup_start,
                        end_time=db_guest.preferred_pickup_end
                    ) if db_guest.preferred_pickup_start and db_guest.preferred_pickup_end else None,
                    special_requirements=db_guest.special_requirements or []
                )
                guests.append(guest)
        
        # 車両情報を取得
        vehicles = []
        for vehicle_id in request.available_vehicle_ids:
            db_vehicle = crud_vehicle.get(db, UUID(vehicle_id))
            if db_vehicle:
                vehicle = Vehicle(
                    id=str(db_vehicle.id),
                    name=db_vehicle.name,
                    capacity_adults=db_vehicle.capacity_adults,
                    capacity_children=db_vehicle.capacity_children,
                    driver_name=db_vehicle.driver_name,
                    vehicle_type=db_vehicle.vehicle_type.value if db_vehicle.vehicle_type else "van",
                    equipment=db_vehicle.equipment or []
                )
                vehicles.append(vehicle)
        
        # ゲストまたは車両が取得できない場合はサンプルデータを使用
        if not guests:
            logger.warning("No guests found in DB, using sample data")
            guests = create_sample_guests(request.participant_ids)
        if not vehicles:
            logger.warning("No vehicles found in DB, using sample data")
            vehicles = create_sample_vehicles(request.available_vehicle_ids)
        
        # 最適化エンジンを取得
        optimization_jobs[job_id].current_step = "最適化実行中"
        optimization_jobs[job_id].progress_percentage = 50
        
        opt = get_optimizer()
        
        if opt:
            # 最適化実行
            result = opt.optimize(request, guests, vehicles)
        else:
            # フォールバック：仮の結果を生成
            result = create_dummy_result(request)
        
        # 結果をDBに保存
        optimization_jobs[job_id].current_step = "結果保存中"
        optimization_jobs[job_id].progress_percentage = 90
        
        if hasattr(request, 'tour_id') and request.tour_id:
            tour_id = UUID(request.tour_id)
        else:
            # tour_idが含まれていない場合は、tour_dateとactivity_typeから特定
            from app.crud.tour import tour as crud_tour
            tours = crud_tour.get_multi(
                db, 
                tour_date=request.tour_date,
                limit=1
            )
            if tours:
                tour_id = tours[0].id
            else:
                # 新規ツアーとして処理する場合
                logger.warning("No tour_id provided and no matching tour found")
                tour_id = None
        
        if tour_id and result.status == "success":
            saved_routes = crud_optimization_result.save_result(
                db, 
                tour_id,
                result
            )
            logger.info(f"Saved {len(saved_routes)} routes to database for tour {tour_id}")
        
        # 結果を保存
        optimization_jobs[job_id].status = "completed"
        optimization_jobs[job_id].result = result
        optimization_jobs[job_id].progress_percentage = 100
        optimization_jobs[job_id].updated_at = datetime.now()
        optimization_jobs[job_id].current_step = "完了"
        
        logger.info(f"Optimization completed: {job_id}")
        
    except Exception as e:
        logger.error(f"Optimization failed for job {job_id}: {str(e)}")
        optimization_jobs[job_id].status = "failed"
        optimization_jobs[job_id].error_message = str(e)
        optimization_jobs[job_id].updated_at = datetime.now()
        optimization_jobs[job_id].current_step = "エラー"


def create_sample_guests(guest_ids: List[str]) -> List[Guest]:
    """サンプルゲストデータを生成（テスト用）"""
    sample_hotels = [
        ("ANAインターコンチネンタル", 24.3969, 124.1531),
        ("フサキビーチリゾート", 24.3667, 124.1389),
        ("グランヴィリオリゾート", 24.4086, 124.1639),
        ("アートホテル", 24.3378, 124.1561),
    ]
    
    guests = []
    for i, guest_id in enumerate(guest_ids):
        hotel = sample_hotels[i % len(sample_hotels)]
        guest = Guest(
            id=guest_id,
            name=f"ゲスト{i+1}",
            hotel_name=hotel[0],
            pickup_location=Location(
                name=hotel[0],
                lat=hotel[1],
                lng=hotel[2]
            ),
            num_adults=2,
            num_children=1 if i % 3 == 0 else 0,
            preferred_time_window=TimeWindow(
                start_time=time(7, 30),
                end_time=time(8, 30)
            ) if i % 2 == 0 else None,
            special_requirements=[]
        )
        guests.append(guest)
    
    return guests


def create_sample_vehicles(vehicle_ids: List[str]) -> List[Vehicle]:
    """サンプル車両データを生成（テスト用）"""
    vehicles = []
    
    for i, vehicle_id in enumerate(vehicle_ids):
        if i % 3 == 0:
            # 大型バス
            vehicle = Vehicle(
                id=vehicle_id,
                name=f"大型バス{i+1}",
                capacity_adults=20,
                capacity_children=5,
                driver_name=f"ドライバー{i+1}",
                vehicle_type="minibus",
                equipment=[]
            )
        elif i % 3 == 1:
            # 中型バン
            vehicle = Vehicle(
                id=vehicle_id,
                name=f"バン{i+1}",
                capacity_adults=10,
                capacity_children=3,
                driver_name=f"ドライバー{i+1}",
                vehicle_type="van",
                equipment=["child_seat"] if i % 4 == 0 else []
            )
        else:
            # 小型車
            vehicle = Vehicle(
                id=vehicle_id,
                name=f"セダン{i+1}",
                capacity_adults=4,
                capacity_children=1,
                driver_name=f"ドライバー{i+1}",
                vehicle_type="sedan",
                equipment=[]
            )
        vehicles.append(vehicle)
    
    return vehicles


def create_dummy_result(request: OptimizationRequest) -> OptimizationResult:
    """ダミーの最適化結果を生成（テスト用）"""
    # 簡単なダミールートを作成
    dummy_route = VehicleRoute(
        vehicle_id=request.available_vehicle_ids[0] if request.available_vehicle_ids else "dummy_vehicle",
        vehicle_name="テスト車両1",
        route_segments=[
            RouteSegment(
                from_location=Location(name="車両基地", lat=24.3448, lng=124.1572),
                to_location=request.destination,
                guest_id=None,
                distance_km=10.5,
                duration_minutes=20,
                arrival_time=time(9, 0),
                departure_time=time(9, 5)
            )
        ],
        assigned_guests=request.participant_ids,
        total_distance_km=10.5,
        total_duration_minutes=20,
        efficiency_score=0.8,
        vehicle_utilization=0.75
    )
    
    return OptimizationResult(
        tour_id=f"tour_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        status="success",
        total_vehicles_used=1,
        routes=[dummy_route],
        total_distance_km=10.5,
        total_time_minutes=20,
        average_efficiency_score=0.8,
        optimization_metrics={"dummy": True},
        warnings=["これはテスト用のダミー結果です"],
        computation_time_seconds=0.1
    )


@router.get("/test-data")
async def get_test_data():
    """テスト用のサンプルデータを返す"""
    return {
        "sample_request": {
            "tour_date": "2024-03-20",
            "activity_type": "snorkeling",
            "destination": {
                "name": "川平湾",
                "lat": 24.4526,
                "lng": 124.1456
            },
            "participant_ids": ["guest001", "guest002", "guest003", "guest004"],
            "available_vehicle_ids": ["vehicle001", "vehicle002"],
            "constraints": {
                "max_pickup_time_minutes": 90,
                "buffer_time_minutes": 15,
                "weather_consideration": True
            },
            "optimization_strategy": "balanced",
            "departure_time": "09:00:00"
        },
        "sample_locations": {
            "hotels": [
                {"name": "ANAインターコンチネンタル", "lat": 24.3969, "lng": 124.1531},
                {"name": "フサキビーチリゾート", "lat": 24.3667, "lng": 124.1389},
                {"name": "グランヴィリオリゾート", "lat": 24.4086, "lng": 124.1639},
                {"name": "アートホテル", "lat": 24.3378, "lng": 124.1561}
            ],
            "destinations": [
                {"name": "川平湾", "lat": 24.4526, "lng": 124.1456},
                {"name": "石垣港", "lat": 24.3345, "lng": 124.1572},
                {"name": "竹富島行き桟橋", "lat": 24.3324, "lng": 124.1547}
            ]
        }
    }