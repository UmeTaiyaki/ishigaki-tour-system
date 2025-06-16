"""
最適化結果のDB保存機能をテスト
"""

import requests
import json
import time
from datetime import datetime

base_url = "http://localhost:8000/api/v1"

print("=== 最適化結果DB保存テスト ===\n")

# 1. 車両を登録
print("1. 車両を登録中...")
vehicle_ids = []
vehicles_data = [
    {
        "name": "テストバン1",
        "capacity_adults": 10,
        "capacity_children": 3,
        "driver_name": "運転手A",
        "vehicle_type": "van",
        "status": "available"
    },
    {
        "name": "テストバン2",
        "capacity_adults": 10,
        "capacity_children": 3,
        "driver_name": "運転手B",
        "vehicle_type": "van",
        "status": "available"
    }
]

for v_data in vehicles_data:
    response = requests.post(f"{base_url}/vehicles/", json=v_data)
    if response.status_code == 200:
        vehicle = response.json()
        vehicle_ids.append(vehicle["id"])
        print(f"✅ {v_data['name']}登録成功: {vehicle['id']}")

# 2. ゲストを登録
print("\n2. ゲストを登録中...")
guest_ids = []
guests_data = [
    {
        "name": "テストゲスト1",
        "hotel_name": "ANAインターコンチネンタル",
        "pickup_lat": 24.3969,
        "pickup_lng": 124.1531,
        "num_adults": 2,
        "num_children": 0
    },
    {
        "name": "テストゲスト2",
        "hotel_name": "フサキビーチリゾート",
        "pickup_lat": 24.3667,
        "pickup_lng": 124.1389,
        "num_adults": 2,
        "num_children": 1
    },
    {
        "name": "テストゲスト3",
        "hotel_name": "グランヴィリオリゾート",
        "pickup_lat": 24.4086,
        "pickup_lng": 124.1639,
        "num_adults": 3,
        "num_children": 0
    }
]

for g_data in guests_data:
    response = requests.post(f"{base_url}/guests/", json=g_data)
    if response.status_code == 200:
        guest = response.json()
        guest_ids.append(guest["id"])
        print(f"✅ {g_data['name']}登録成功: {guest['id']}")

# 3. ツアーを作成
print("\n3. ツアーを作成中...")
tour_data = {
    "tour_date": "2024-06-25",
    "activity_type": "snorkeling",
    "destination_name": "川平湾",
    "destination_lat": 24.4526,
    "destination_lng": 124.1456,
    "departure_time": "09:00:00",
    "participant_ids": guest_ids,
    "vehicle_ids": vehicle_ids
}

response = requests.post(f"{base_url}/tours/", json=tour_data)
if response.status_code == 200:
    tour = response.json()
    tour_id = tour["id"]
    print(f"✅ ツアー作成成功: {tour_id}")
else:
    print(f"❌ ツアー作成失敗: {response.status_code}")
    print(response.text)
    exit(1)

# 4. ツアーの最適化を実行
print(f"\n4. ツアー {tour_id} の最適化を実行中...")
response = requests.post(f"{base_url}/tours/{tour_id}/optimize")
if response.status_code == 200:
    result = response.json()
    job_id = result["job_id"]
    print(f"✅ 最適化ジョブ開始: {job_id}")
    
    # 5. 最適化の完了を待つ
    print("\n5. 最適化の完了を待っています...")
    max_attempts = 10
    for i in range(max_attempts):
        time.sleep(2)
        response = requests.get(f"{base_url}/optimize/status/{job_id}")
        if response.status_code == 200:
            status = response.json()
            print(f"   状態: {status['status']} (進捗: {status['progress_percentage']}%)")
            
            if status['status'] == 'completed':
                print("✅ 最適化完了！")
                break
            elif status['status'] == 'failed':
                print(f"❌ 最適化失敗: {status.get('error_message', 'Unknown error')}")
                exit(1)
    
    # 6. 最適化結果を取得
    print("\n6. 最適化結果を取得中...")
    response = requests.get(f"{base_url}/optimize/result/{job_id}")
    if response.status_code == 200:
        optimization_result = response.json()
        print("✅ 最適化結果:")
        print(f"   - 状態: {optimization_result['status']}")
        print(f"   - 使用車両数: {optimization_result['total_vehicles_used']}")
        print(f"   - 総走行距離: {optimization_result['total_distance_km']} km")
        print(f"   - 総所要時間: {optimization_result['total_time_minutes']} 分")
    
    # 7. DBに保存された結果を確認
    print("\n7. DBに保存された最適化結果を確認中...")
    response = requests.get(f"{base_url}/tours/{tour_id}/optimization-result")
    if response.status_code == 200:
        saved_result = response.json()
        print("✅ DB保存確認:")
        print(f"   - ツアーID: {saved_result['tour_id']}")
        print(f"   - ツアー日付: {saved_result['tour_date']}")
        print(f"   - 目的地: {saved_result['destination']}")
        print(f"   - ルート数: {len(saved_result['routes'])}")
        print(f"   - 最適化実行時刻: {saved_result['optimized_at']}")
        
        # ルートの詳細を表示
        for i, route in enumerate(saved_result['routes']):
            print(f"\n   ルート{i+1} ({route['vehicle_name']}):")
            print(f"     - 走行距離: {route['total_distance_km']} km")
            print(f"     - 所要時間: {route['total_time_minutes']} 分")
            print(f"     - 乗客数: {len(route['assigned_guests'])}")
    else:
        print(f"❌ DB結果取得失敗: {response.status_code}")
        print(response.text)
        
else:
    print(f"❌ 最適化開始失敗: {response.status_code}")
    print(response.text)

# 8. クリーンアップ
print("\n8. クリーンアップ中...")
# ツアーを削除（関連する最適化結果も削除される）
response = requests.delete(f"{base_url}/tours/{tour_id}")
if response.status_code == 200:
    print(f"✅ ツアー {tour_id} を削除しました")

# 車両を削除
for vehicle_id in vehicle_ids:
    response = requests.delete(f"{base_url}/vehicles/{vehicle_id}")
    if response.status_code == 200:
        print(f"✅ 車両 {vehicle_id} を削除しました")

# ゲストを削除
for guest_id in guest_ids:
    response = requests.delete(f"{base_url}/guests/{guest_id}")
    if response.status_code == 200:
        print(f"✅ ゲスト {guest_id} を削除しました")

print("\n✅ テスト完了！")