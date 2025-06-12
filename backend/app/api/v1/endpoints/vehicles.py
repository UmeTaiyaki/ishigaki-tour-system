"""
車両管理APIエンドポイント
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.vehicle import VehicleStatus
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse
from app.crud.vehicle import vehicle as crud_vehicle

router = APIRouter()


@router.get("/", response_model=List[VehicleResponse])
def read_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[VehicleStatus] = Query(None, description="車両のステータスでフィルタ"),
    db: Session = Depends(get_db)
):
    """
    車両一覧を取得
    
    - **skip**: スキップする件数
    - **limit**: 取得する最大件数
    - **status**: 車両ステータス（available, in_use, maintenance）
    """
    vehicles = crud_vehicle.get_multi(db, skip=skip, limit=limit, status=status)
    return vehicles


@router.post("/", response_model=VehicleResponse)
def create_vehicle(
    vehicle_in: VehicleCreate,
    db: Session = Depends(get_db)
):
    """
    新しい車両を作成
    """
    return crud_vehicle.create(db=db, obj_in=vehicle_in)


@router.get("/available", response_model=List[VehicleResponse])
def read_available_vehicles(
    db: Session = Depends(get_db)
):
    """
    利用可能な車両のみを取得
    """
    return crud_vehicle.get_available(db=db)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def read_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db)
):
    """
    特定の車両情報を取得
    """
    vehicle = crud_vehicle.get(db=db, vehicle_id=vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: UUID,
    vehicle_in: VehicleUpdate,
    db: Session = Depends(get_db)
):
    """
    車両情報を更新
    """
    vehicle = crud_vehicle.get(db=db, vehicle_id=vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return crud_vehicle.update(db=db, db_obj=vehicle, obj_in=vehicle_in)


@router.delete("/{vehicle_id}", response_model=VehicleResponse)
def delete_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db)
):
    """
    車両を削除
    """
    vehicle = crud_vehicle.get(db=db, vehicle_id=vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return crud_vehicle.delete(db=db, vehicle_id=vehicle_id)


@router.get("/by-capacity/", response_model=List[VehicleResponse])
def read_vehicles_by_capacity(
    min_adults: int = Query(..., ge=1, description="必要な大人の最小席数"),
    min_children: int = Query(0, ge=0, description="必要な子供の最小席数"),
    db: Session = Depends(get_db)
):
    """
    必要な容量を満たす車両を検索
    """
    return crud_vehicle.get_by_capacity(
        db=db, 
        min_adults=min_adults, 
        min_children=min_children
    )