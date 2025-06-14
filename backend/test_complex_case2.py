"""
複雑なテストケース2: 厳しい時間制約
- 狭い時間窓
- 分散したホテル
- 車両容量ギリギリ
"""

import requests
import json
from datetime import datetime, time
import time as time_module

base_url = "http://localhost:8000/api/v1"

print("=== 複雑なテストケース2: 厳しい時間制約 ===\n")

# 車両は2台のみ（容量制限を厳しく）
vehicles_data = [
    {
        "name": "中型バン1",
        "capacity_adults": 8,
        "capacity_children": 2,
        "driver_name": "運転手A",
        "vehicle_type": "van",
        "status": "available"
    },
    {
        "name": "中型バン2",
        "capacity_adults": 8,
        "capacity_children": 2,
        "driver_name": "運転手B",
        "vehicle_type": "van",
        "status": "available"
    }
]

print("車両を登録中...")
vehicle_ids = []
for v_data in vehicles_data:
    response = requests.post(f"{base_url}/vehicles/", json=v_data)
    if response.status_code == 200:
        vehicle = response.json()
        vehicle_ids.append(vehicle["id"])
        print(f"✅ {v_data['name']}登録成功")

# ホテルの座標
hotel_coords = {
    "ANAインターコンチネンタル": (24.3969, 124.1531),
    "フサキビーチリゾート": (24.3667, 124.1389),
    "グランヴィリオリゾート": (24.4086, 124.1639),
    "アートホテル": (24.3378, 124.1561),
    "石垣シーサイドホテル": (24.3542, 124.1689),
    "川平ベイリゾート": (24.4426, 124.1456)
}

# 狭い時間窓を持つゲスト
guests_data = [
    # 早朝グループ（7:00-7:15の狭い窓）
    {"name": "早朝1", "hotel": "ANAインターコンチネンタル", "adults": 2, "children": 0, "time_start": "07:00", "time_end": "07:15"},
    {"name": "早朝2", "hotel": "フサキビーチリゾート", "adults": 2, "children": 1, "time_start": "07:00", "time_end": "07:15"},
    {"name": "早朝3", "hotel": "グランヴィリオリゾート", "adults": 3, "children": 0, "time_start": "07:05", "time_end": "07:20"},
    
    # 中間グループ（7:30-7:45）
    {"name": "中間1", "hotel": "アートホテル", "adults": 2, "children": 1, "time_start": "07:30", "time_end": "07:45"},
    {"name": "中間2", "hotel": "石垣シーサイドホテル", "adults": 3, "children": 0, "time_start": "07:30", "time_end": "07:45"},
    {"name": "中間3", "hotel": "ANAインターコンチネンタル", "adults": 2, "children": 0, "time_start": "07:35", "time_end": "07:50"},
    
    # 遅めグループ（8:00-8:15）
    {"name": "遅め1", "hotel": "川平ベイリゾート", "adults": 2, "children": 0, "time_start": "08:00", "time_end": "08:15"},
    {"name": "遅め2", "hotel": "フサキビーチリゾート", "adults": 3, "children": 1, "time_start": "08:00", "time_end": "08:15"},
    {"name": "遅め3", "hotel": "グランヴィリオリゾート", "adults": 1, "children": 0, "time_start": "08:05", "time_end": "08:20"},
]

print("\nゲストを登録中...")
guest_ids = []
total_adults = 0
total_children = 0

for g_data in guests_data:
    coords = hotel_coords[g_data["hotel"]]
    guest_request = {
        "name": g_data["name"],
        "hotel_name": g_data["hotel"],
        "pickup_lat": coords[0],
        "pickup_lng": coords[1],
        "num_adults": g_data["adults"],
        "num_children": g_data["children"],
        "special_requirements": []
    }
    
    if g_data["time_start"] and g_data["time_end"]:
        guest_request["preferred_pickup_start"] = g_data["time_start"] + ":00"
        guest_request["preferred_pickup_end"] = g_data["time_end"] + ":00"
    
    response = requests.post(f"{base_url}/guests/", json=guest_request)
    if response.status_code == 200:
        guest = response.json()
        guest_ids.append(guest["id"])
        total_adults += g_data["adults"]
        total_children += g_data["children"]
        print(f"✅ {g_data['name']}登録成功")

print(f"\n登録完了:")
print(f"- ゲスト数: {len(guest_ids)}名")
print(f"- 大人: {total_adults}名, 子供: {total_children}名")
print(f"- 総乗客数: {total_adults + total_children}名")
print(f"- 車両総容量: {16}名（大人）+ {4}名（子供）")

# 容量チェック
if total_adults > 16:
    print("⚠️ 警告: 大人の総数が車両容量を超えています！")

# 最適化を実行
print(f"\n\n=== 最適化実行 ===")

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
    "constraints": {
        "max_pickup_time_minutes": 90,
        "buffer_time_minutes": 5,  # バッファを短く
        "weather_consideration": False
    },
    "optimization_strategy": "balanced",
    "departure_time": "09:00:00"
}

response = requests.post(f"{base_url}/optimize/route", json=optimization_data)
if response.status_code == 200:
    job = response.json()
    job_id = job["job_id"]
    print(f"最適化ジョブ開始: {job_id}")
    
    # 結果を待機
    print("結果を待機中...")
    time_module.sleep(5)
    
    response = requests.get(f"{base_url}/optimize/result/{job_id}")
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n結果サマリー:")
        print(f"- 状態: {result['status']}")
        print(f"- 使用車両数: {result['total_vehicles_used']}台")
        print(f"- 総走行距離: {result['total_distance_km']} km")
        print(f"- 総所要時間: {result['total_time_minutes']} 分")
        print(f"- 平均効率性: {result['average_efficiency_score']}")
        print(f"- 計算時間: {result['computation_time_seconds']:.3f}秒")
        
        # 時間制約の検証
        print("\n=== 時間制約の検証 ===")
        all_constraints_met = True
        
        for route in result['routes']:
            print(f"\n車両: {route['vehicle_name']}")
            for segment in route['route_segments']:
                if segment['guest_id']:
                    # ゲストの時間窓を確認
                    guest_data = next((g for g in guests_data if guest_ids[guests_data.index(g)] == segment['guest_id']), None)
                    if guest_data and guest_data['time_start']:
                        arrival_time = datetime.strptime(segment['arrival_time'], "%H:%M:%S").time()
                        window_start = datetime.strptime(guest_data['time_start'] + ":00", "%H:%M:%S").time()
                        window_end = datetime.strptime(guest_data['time_end'] + ":00", "%H:%M:%S").time()
                        
                        if arrival_time < window_start or arrival_time > window_end:
                            print(f"  ❌ {guest_data['name']}: 到着 {arrival_time} (希望 {window_start}-{window_end})")
                            all_constraints_met = False
                        else:
                            print(f"  ✅ {guest_data['name']}: 到着 {arrival_time} (希望 {window_start}-{window_end})")
        
        if all_constraints_met:
            print("\n✅ すべての時間制約を満たしています！")
        else:
            print("\n⚠️ 一部の時間制約を満たせませんでした")
        
        # 結果を保存
        filename = "complex_result_time_constraints.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 結果を{filename}に保存しました")
    else:
        print(f"❌ 結果取得失敗: {response.status_code}")
        print(response.text)
else:
    print(f"❌ 最適化失敗: {response.status_code}")
    print(response.text)

# クリーンアップ
print("\n\nクリーンアップ中...")
for vehicle_id in vehicle_ids:
    requests.delete(f"{base_url}/vehicles/{vehicle_id}")
for guest_id in guest_ids:
    requests.delete(f"{base_url}/guests/{guest_id}")
print("✅ クリーンアップ完了")