"""
ツアー作成のデバッグテスト
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, time
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.database import SessionLocal, engine
from app.models.tour import Tour, ActivityType, TourStatus
from app.models.tour_participant import TourParticipant
from app.crud.tour import tour as crud_tour
from app.schemas.tour import TourCreate


def test_direct_creation():
    """データベースに直接ツアーを作成してテスト"""
    db = SessionLocal()
    
    try:
        # テスト用のツアーデータ
        print("=== Direct Database Creation Test ===")
        
        # ツアーを直接作成
        new_tour = Tour(
            tour_date=date(2024, 6, 20),
            activity_type=ActivityType.snorkeling,
            destination_name="川平湾",
            destination_lat=24.4526,
            destination_lng=124.1456,
            departure_time=time(9, 0),
            status=TourStatus.planning,
            optimization_strategy="balanced"
        )
        
        db.add(new_tour)
        db.flush()
        print(f"✅ Tour created with ID: {new_tour.id}")
        
        # 参加者を追加
        participant_ids = [
            "4e70ad1f-39c7-4962-806d-aaacb7227935",
            "1a80cd57-9f26-45af-82bb-2bf324650c61"
        ]
        
        for idx, guest_id in enumerate(participant_ids):
            participant = TourParticipant(
                tour_id=new_tour.id,
                guest_id=UUID(guest_id),
                pickup_order=idx + 1
            )
            db.add(participant)
            print(f"✅ Added participant: {guest_id}")
        
        db.commit()
        print("✅ Successfully created tour with participants")
        
        # 作成したツアーを確認
        created_tour = db.query(Tour).filter(Tour.id == new_tour.id).first()
        print(f"\nCreated tour:")
        print(f"  ID: {created_tour.id}")
        print(f"  Date: {created_tour.tour_date}")
        print(f"  Participants: {len(created_tour.participants)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def test_crud_creation():
    """CRUDを使用したツアー作成テスト"""
    db = SessionLocal()
    
    try:
        print("\n=== CRUD Creation Test ===")
        
        # TourCreateスキーマを作成
        tour_data = TourCreate(
            tour_date=date(2024, 6, 21),
            activity_type=ActivityType.diving,
            destination_name="マンタポイント",
            destination_lat=24.4000,
            destination_lng=124.1500,
            departure_time=time(8, 0),
            status=TourStatus.planning,
            optimization_strategy="safety",
            participant_ids=[
                UUID("4e70ad1f-39c7-4962-806d-aaacb7227935"),
                UUID("8d5f6a7b-48b9-41e7-9974-5f70e4c85722")
            ]
        )
        
        # CRUDで作成
        created_tour = crud_tour.create(
            db=db,
            obj_in=tour_data,
            participant_ids=tour_data.participant_ids
        )
        
        print(f"✅ Tour created with CRUD")
        print(f"  ID: {created_tour.id}")
        print(f"  Participants: {len(created_tour.participants)}")
        
    except Exception as e:
        print(f"❌ CRUD Error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def check_database_tables():
    """データベーステーブルの存在確認"""
    print("\n=== Database Tables Check ===")
    
    from sqlalchemy import inspect
    inspector = inspect(engine)
    
    tables = inspector.get_table_names()
    print(f"Existing tables: {tables}")
    
    # 各テーブルのカラムを確認
    for table in ['tours', 'tour_participants', 'guests']:
        if table in tables:
            columns = inspector.get_columns(table)
            print(f"\n{table} columns:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")


if __name__ == "__main__":
    check_database_tables()
    test_direct_creation()
    test_crud_creation()