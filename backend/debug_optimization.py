"""
最適化の詳細デバッグスクリプト
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, time, datetime, timedelta
from app.optimizer.route_optimizer import RouteOptimizer
from app.schemas.optimization import OptimizationRequest, Guest, Vehicle, Location, TimeWindow
import logging

# ログレベルを設定
logging.basicConfig(level=logging.DEBUG)

# シンプルなテストケース
guests = [
    Guest(
        id="guest1",
        name="ゲスト1",
        hotel_name="ホテルA",
        pickup_location=Location(name="ホテルA", lat=24.3969, lng=124.1531),
        num_adults=2,
        num_children=0,
        preferred_time_window=None,  # 時間窓なし
        special_requirements=[]
    ),
    Guest(
        id="guest2",
        name="ゲスト2",
        hotel_name="ホテルB",
        pickup_location=Location(name="ホテルB", lat=24.3667, lng=124.1389),
        num_adults=2,
        num_children=0,
        preferred_time_window=None,  # 時間窓なし
        special_requirements=[]
    )
]

vehicles = [
    Vehicle(
        id="vehicle1",
        name="テスト車両",
        capacity_adults=10,
        capacity_children=3,
        driver_name="ドライバー",
        vehicle_type="van",
        equipment=[]
    )
]

request = OptimizationRequest(
    tour_date=date(2024, 6, 20),
    activity_type="snorkeling",
    destination=Location(name="川平湾", lat=24.4526, lng=124.1456),
    participant_ids=[g.id for g in guests],
    available_vehicle_ids=[v.id for v in vehicles],
    optimization_strategy="balanced",
    departure_time=time(9, 0)
)

# 最適化実行
print("=== シンプルなケースでのデバッグ ===")
optimizer = RouteOptimizer()

# データ準備を確認
data = optimizer._prepare_data(request, guests, vehicles)
print("\n距離行列:")
for i, row in enumerate(data['distance_matrix']):
    print(f"{data['location_names'][i]:20} {row}")

print("\n時間行列（分）:")
for i, row in enumerate(data['time_matrix']):
    print(f"{data['location_names'][i]:20} {row}")

print("\n時間窓:")
for i, (name, window) in enumerate(zip(data['location_names'], data['time_windows'])):
    start_time = (datetime.combine(date.today(), time(6, 0)) + timedelta(minutes=window[0])).time()
    end_time = (datetime.combine(date.today(), time(6, 0)) + timedelta(minutes=window[1])).time()
    print(f"{name:20} {window} ({start_time} - {end_time})")

# 最適化実行
result = optimizer.optimize(request, guests, vehicles)

# 結果表示
print("\n=== 最適化結果 ===")
print(f"状態: {result.status}")
print(f"総走行距離: {result.total_distance_km} km")
print(f"総所要時間: {result.total_time_minutes} 分")

for route in result.routes:
    print(f"\n車両: {route.vehicle_name}")
    cumulative_time = 0
    for i, segment in enumerate(route.route_segments):
        print(f"\n{i+1}. {segment.from_location.name} → {segment.to_location.name}")
        print(f"   出発: {segment.departure_time} / 到着: {segment.arrival_time}")
        print(f"   距離: {segment.distance_km} km / 時間: {segment.duration_minutes} 分")
        
        # 累積時間の確認
        cumulative_time += segment.duration_minutes
        expected_arrival = (datetime.combine(date.today(), time(6, 0)) + timedelta(minutes=cumulative_time)).time()
        print(f"   累積時間: {cumulative_time}分 (期待到着: {expected_arrival})")