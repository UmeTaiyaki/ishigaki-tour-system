"""
ゲスト管理APIエンドポイント
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.schemas.guest import GuestCreate, GuestUpdate, GuestResponse
from app.crud.guest import guest as crud_guest

router = APIRouter()


@router.get("/", response_model=List[GuestResponse])
def read_guests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="名前、ホテル名、メールで検索"),
    db: Session = Depends(get_db)
):
    """
    ゲスト一覧を取得
    
    - **skip**: スキップする件数
    - **limit**: 取得する最大件数
    - **search**: 検索文字列（名前、ホテル名、メールアドレスで部分一致検索）
    """
    guests = crud_guest.get_multi(db, skip=skip, limit=limit, search=search)
    return guests


@router.post("/", response_model=GuestResponse)
def create_guest(
    guest_in: GuestCreate,
    db: Session = Depends(get_db)
):
    """
    新しいゲストを作成
    """
    return crud_guest.create(db=db, obj_in=guest_in)


@router.get("/{guest_id}", response_model=GuestResponse)
def read_guest(
    guest_id: UUID,
    db: Session = Depends(get_db)
):
    """
    特定のゲスト情報を取得
    """
    guest = crud_guest.get(db=db, guest_id=guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest


@router.put("/{guest_id}", response_model=GuestResponse)
def update_guest(
    guest_id: UUID,
    guest_in: GuestUpdate,
    db: Session = Depends(get_db)
):
    """
    ゲスト情報を更新
    """
    guest = crud_guest.get(db=db, guest_id=guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return crud_guest.update(db=db, db_obj=guest, obj_in=guest_in)


@router.delete("/{guest_id}", response_model=GuestResponse)
def delete_guest(
    guest_id: UUID,
    db: Session = Depends(get_db)
):
    """
    ゲストを削除
    """
    guest = crud_guest.get(db=db, guest_id=guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return crud_guest.delete(db=db, guest_id=guest_id)


@router.get("/by-hotel/{hotel_name}", response_model=List[GuestResponse])
def read_guests_by_hotel(
    hotel_name: str,
    db: Session = Depends(get_db)
):
    """
    ホテル名でゲストを検索
    """
    return crud_guest.get_by_hotel(db=db, hotel_name=hotel_name)