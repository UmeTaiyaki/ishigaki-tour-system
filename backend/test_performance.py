"""
パフォーマンステスト: 処理速度と最適化品質の測定
"""

import requests
import time
import json
import statistics
from datetime import datetime
import random

base_url = "http://localhost:8000/api/v1"

test_sizes = [5, 10, 20, 30]  # ゲスト数（50は時間がかかりすぎる可能性があるので一旦除外）
results = []

print("=== パフォーマンステスト ===\n")

# ホテルの座標リスト
hotel_list = [
    ("ANAインターコンチネンタル", 24.3969, 124.1531),
    ("フサキビーチリゾート", 24.3667, 124.1389),
    ("グランヴィリオリゾート", 24.4086, 124.1639),
    ("アートホテル", 24.3378, 124.1561),
    ("石垣シーサイドホテル", 24.3542, 124.1689),
    ("川平ベイリゾート", 24.4426, 124.1456)
]

for size in test_sizes:
    print(f"\nテストサイズ: {size}名")
    
    # 車両を生成（サイズに応じて調整）
    num_vehicles = max(2, (size // 10) + 1)
    vehicle_ids = []
    
    for i in range(num_vehicles):
        vehicle_data = {
            "name": f"テスト車両{i+1}",
            "capacity_adults": 10,
            "capacity_children": 3,
            "driver_name": f"運転手{i+1}",
            "vehicle_type": "van",
            "status": "available"
        }
        response = requests.post(f"{base_url}/vehicles/", json=vehicle_data)
        if response.status_code == 200:
            vehicle_ids.append(response.json()["id"])
    
    # ゲストを生成
    guest_ids = []
    for i in range(size):
        hotel = random.choice(hotel_list)
        guest_data = {
            "name": f"テストゲスト{i+1}",
            "hotel_name": hotel[0],
            "pickup_lat": hotel[1],
            "pickup_lng": hotel[2],
            "num_adults": random.randint(1, 3),
            "num_children": random.randint(0, 1),
            "special_requirements": []
        }
        response = requests.post(f"{base_url}/guests/", json=guest_data)
        if response.status_code == 200:
            guest_ids.append(response.json()["id"])
    
    # 最適化を5回実行して平均を取る
    computation_times = []
    distances = []
    success_count = 0
    
    for i in range(5):
        start_time = time.time()
        
        # 最適化実行
        optimization_data = {
            "tour_date": "2024-06-20",
            "activity_type": "snorkeling",
            "destination": {
                "name": "川平湾",
                "lat": 24.4526,
                "lng": 124.1456
            },
            "participant_ids": guest_ids,
            "available_vehicle_ids": vehicle_ids,
            "optimization_strategy": "balanced",
            "departure_time": "09:00:00"
        }
        
        response = requests.post(f"{base_url}/optimize/route", json=optimization_data)
        if response.status_code == 200:
            job_id = response.json()["job_id"]
            
            # 結果を待機
            time.sleep(2)
            
            result_response = requests.get(f"{base_url}/optimize/result/{job_id}")
            if result_response.status_code == 200:
                result = result_response.json()
                if result['status'] == 'success':
                    success_count += 1
                    distances.append(result['total_distance_km'])
                    computation_times.append(result['computation_time_seconds'])
        
        end_time = time.time()
        total_time = end_time - start_time
        print(f"  試行{i+1}: {total_time:.3f}秒")
    
    if computation_times:
        avg_time = statistics.mean(computation_times)
        std_time = statistics.stdev(computation_times) if len(computation_times) > 1 else 0
        avg_distance = statistics.mean(distances)
        
        print(f"  成功率: {success_count}/5")
        print(f"  平均計算時間: {avg_time:.3f}秒 (±{std_time:.3f})")
        print(f"  最大計算時間: {max(computation_times):.3f}秒")
        print(f"  平均走行距離: {avg_distance:.2f} km")
        
        results.append({
            "size": size,
            "avg_time": avg_time,
            "max_time": max(computation_times),
            "avg_distance": avg_distance,
            "success_rate": success_count / 5
        })
    
    # クリーンアップ
    for vehicle_id in vehicle_ids:
        requests.delete(f"{base_url}/vehicles/{vehicle_id}")
    for guest_id in guest_ids:
        requests.delete(f"{base_url}/guests/{guest_id}")

# 結果を保存
with open("performance_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n=== パフォーマンステスト完了 ===")
print("\n結果サマリー:")
for r in results:
    print(f"- {r['size']}名: 平均{r['avg_time']:.3f}秒, 最大{r['max_time']:.3f}秒")