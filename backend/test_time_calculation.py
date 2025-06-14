import requests
import json
from datetime import datetime, timedelta
import time as time_module

# ベースURL
base_url = "http://localhost:8000/api/v1"

print("=== 石垣島ツアー最適化 - 時刻計算テスト ===\n")

# 1. 複数の車両を登録
vehicles = []
vehicle_data_list = [
    {
        "name": "大型バス1",
        "capacity_adults": 20,
        "capacity_children": 5,
        "driver_name": "運転手A",
        "status": "available",
        "vehicle_type": "minibus"
    },
    {
        "name": "中型バン1",
        "capacity_adults": 10,
        "capacity_children": 3,
        "driver_name": "運転手B",
        "status": "available",
        "vehicle_type": "van"
    }
]

print("車両を登録中...")
for vehicle_data in vehicle_data_list:
    response = requests.post(f"{base_url}/vehicles/", json=vehicle_data)
    if response.status_code == 200:
        vehicle = response.json()
        vehicles.append(vehicle["id"])
        print(f"✅ {vehicle_data['name']}登録成功: {vehicle['id']}")
    else:
        print(f"❌ 車両登録失敗: {response.text}")

# 2. 既存のゲストIDを使用（実際のIDに置き換えてください）
guest_ids = [
    "4e70ad1f-39c7-4962-806d-aaacb7227935",  # 田中太郎
    "1a80cd57-9f26-45af-82bb-2bf324650c61",  # 山田花子
    "8d5f6a7b-48b9-41e7-9974-5f70e4c85722",  # 佐藤次郎
    "4aa1a21a-ce53-4487-9c94-33b247949576"   # 鈴木美咲
]

# 3. 最適化を実行（出発時刻を9:00に設定）
optimization_data = {
    "tour_date": "2024-06-20",
    "activity_type": "snorkeling",
    "destination": {
        "name": "川平湾",
        "lat": 24.4526,
        "lng": 124.1456
    },
    "participant_ids": guest_ids,
    "available_vehicle_ids": vehicles,
    "constraints": {
        "max_pickup_time_minutes": 90,
        "buffer_time_minutes": 15,
        "weather_consideration": False
    },
    "optimization_strategy": "efficiency",
    "departure_time": "09:00:00"
}

print(f"\n最適化を実行中...")
print(f"- ゲスト数: {len(guest_ids)}")
print(f"- 車両数: {len(vehicles)}")
print(f"- 出発希望時刻: {optimization_data['departure_time']}")

response = requests.post(f"{base_url}/optimize/route", json=optimization_data)
if response.status_code == 200:
    result = response.json()
    job_id = result["job_id"]
    print(f"✅ 最適化ジョブ開始: {job_id}")
    
    # 4. 結果を取得（少し待機）
    print("結果を待機中...")
    time_module.sleep(3)
    
    response = requests.get(f"{base_url}/optimize/result/{job_id}")
    if response.status_code == 200:
        optimization_result = response.json()
        
        print("\n=== 最適化結果 ===")
        print(f"総走行距離: {optimization_result['total_distance_km']} km")
        print(f"総所要時間: {optimization_result['total_time_minutes']} 分")
        print(f"使用車両数: {optimization_result['total_vehicles_used']} 台")
        
        # 各車両のルートを詳細表示
        for i, route in enumerate(optimization_result['routes']):
            print(f"\n--- 車両 {i+1}: {route['vehicle_name']} ---")
            print(f"走行距離: {route['total_distance_km']} km")
            print(f"所要時間: {route['total_duration_minutes']} 分")
            print(f"乗車率: {route['vehicle_utilization'] * 100:.1f}%")
            
            print("\nルート詳細:")
            for j, segment in enumerate(route['route_segments']):
                from_loc = segment['from_location']['name']
                to_loc = segment['to_location']['name']
                arrival = segment['arrival_time']
                departure = segment['departure_time']
                distance = segment['distance_km']
                duration = segment['duration_minutes']
                
                print(f"{j+1}. {from_loc} → {to_loc}")
                print(f"   到着: {arrival} / 出発: {departure}")
                print(f"   距離: {distance} km / 時間: {duration} 分")
                
                if segment['guest_id']:
                    print(f"   ピックアップゲスト: ID {segment['guest_id']}")
        
        # === 時刻計算の検証 ===
        print("\n=== 時刻計算の検証 ===")
        for route in optimization_result['routes']:
            print(f"\n車両: {route['vehicle_name']}")
            
            # 最初のセグメントの出発時刻から累積時間を計算
            if route['route_segments']:
                first_departure = datetime.strptime(route['route_segments'][0]['departure_time'], "%H:%M:%S")
                base_minutes = first_departure.hour * 60 + first_departure.minute
                
                cumulative_minutes = base_minutes
                
                for i, segment in enumerate(route['route_segments']):
                    arrival_time = datetime.strptime(segment['arrival_time'], "%H:%M:%S")
                    expected_minutes = cumulative_minutes + segment['duration_minutes']
                    expected_arrival = datetime(2000, 1, 1, expected_minutes // 60, expected_minutes % 60)
                    
                    actual_minutes = arrival_time.hour * 60 + arrival_time.minute
                    
                    if abs(actual_minutes - expected_minutes) > 1:  # 1分の誤差を許容
                        print(f"⚠️ 時刻のずれ検出:")
                        print(f"   場所: {segment['to_location']['name']}")
                        print(f"   実際の到着時刻: {segment['arrival_time']}")
                        print(f"   期待される到着時刻: {expected_arrival.strftime('%H:%M:%S')}")
                    else:
                        print(f"✅ {segment['to_location']['name']}: 時刻計算正確")
                    
                    # 次のセグメントのために累積時間を更新
                    if i < len(route['route_segments']) - 1:
                        next_departure = datetime.strptime(route['route_segments'][i+1]['departure_time'], "%H:%M:%S")
                        cumulative_minutes = next_departure.hour * 60 + next_departure.minute
        
        # JSON形式で保存
        with open('optimization_result.json', 'w', encoding='utf-8') as f:
            json.dump(optimization_result, f, ensure_ascii=False, indent=2)
        print("\n✅ 結果をoptimization_result.jsonに保存しました")
        
    else:
        print(f"❌ 結果取得失敗: {response.text}")
else:
    print(f"❌ 最適化失敗: {response.text}")

# 5. クリーンアップ（登録した車両を削除）
print("\nクリーンアップ中...")
for vehicle_id in vehicles:
    response = requests.delete(f"{base_url}/vehicles/{vehicle_id}")
    if response.status_code == 200:
        print(f"✅ 車両 {vehicle_id} を削除しました")