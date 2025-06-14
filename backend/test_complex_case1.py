"""
複雑なテストケース1: 大規模グループの最適化
- 20名のゲスト
- 3台の車両
- 時間窓制約あり
- 特別な要求事項あり
"""

import requests
import json
from datetime import datetime, time
import time as time_module

base_url = "http://localhost:8000/api/v1"

print("=== 複雑なテストケース1: 大規模グループ最適化 ===\n")

# 1. 多様な車両を登録
vehicles_data = [
    {
        "name": "大型バス1",
        "capacity_adults": 20,
        "capacity_children": 5,
        "driver_name": "運転手A",
        "vehicle_type": "minibus",
        "equipment": ["child_seat", "wheelchair_accessible"],
        "status": "available"
    },
    {
        "name": "中型バン1",
        "capacity_adults": 10,
        "capacity_children": 3,
        "driver_name": "運転手B",
        "vehicle_type": "van",
        "equipment": ["child_seat"],
        "status": "available"
    },
    {
        "name": "中型バン2",
        "capacity_adults": 10,
        "capacity_children": 3,
        "driver_name": "運転手C",
        "vehicle_type": "van",
        "equipment": [],
        "status": "available"
    },
    {
        "name": "小型車1",
        "capacity_adults": 4,
        "capacity_children": 1,
        "driver_name": "運転手D",
        "vehicle_type": "sedan",
        "equipment": [],
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

# 2. 多様なゲストを登録
guests_data = [
    # グループ1: ANAインターコンチネンタル（朝早い希望）
    {"name": "田中太郎", "hotel": "ANAインターコンチネンタル", "adults": 2, "children": 0, "time_start": "07:00", "time_end": "07:30"},
    {"name": "田中花子", "hotel": "ANAインターコンチネンタル", "adults": 2, "children": 1, "time_start": "07:00", "time_end": "07:30"},
    {"name": "山田一郎", "hotel": "ANAインターコンチネンタル", "adults": 1, "children": 0, "time_start": "07:15", "time_end": "07:45"},
    
    # グループ2: フサキビーチリゾート（時間に余裕）
    {"name": "佐藤次郎", "hotel": "フサキビーチリゾート", "adults": 2, "children": 2, "time_start": "07:30", "time_end": "08:30"},
    {"name": "佐藤美咲", "hotel": "フサキビーチリゾート", "adults": 2, "children": 0, "time_start": "07:30", "time_end": "08:30"},
    {"name": "鈴木健", "hotel": "フサキビーチリゾート", "adults": 3, "children": 1, "time_start": None, "time_end": None},
    
    # グループ3: グランヴィリオリゾート
    {"name": "高橋洋子", "hotel": "グランヴィリオリゾート", "adults": 2, "children": 0, "time_start": "08:00", "time_end": "08:30"},
    {"name": "伊藤大輔", "hotel": "グランヴィリオリゾート", "adults": 4, "children": 0, "time_start": None, "time_end": None},
    {"name": "渡辺真理", "hotel": "グランヴィリオリゾート", "adults": 1, "children": 1, "time_start": "07:45", "time_end": "08:15"},
    
    # グループ4: アートホテル（遅めの希望）
    {"name": "中村光", "hotel": "アートホテル", "adults": 2, "children": 0, "time_start": "08:15", "time_end": "08:45"},
    {"name": "小林香", "hotel": "アートホテル", "adults": 3, "children": 2, "time_start": "08:00", "time_end": "08:30"},
    
    # グループ5: 石垣シーサイドホテル（新規）
    {"name": "加藤隆", "hotel": "石垣シーサイドホテル", "adults": 2, "children": 0, "time_start": None, "time_end": None},
    {"name": "木村恵", "hotel": "石垣シーサイドホテル", "adults": 1, "children": 0, "time_start": "07:30", "time_end": "08:00"},
    
    # グループ6: 離れた場所のホテル
    {"name": "青木剛", "hotel": "川平ベイリゾート", "adults": 2, "children": 1, "time_start": "07:00", "time_end": "07:30"},
    {"name": "村上友美", "hotel": "川平ベイリゾート", "adults": 2, "children": 0, "time_start": None, "time_end": None},
]

# ホテルの座標
hotel_coords = {
    "ANAインターコンチネンタル": (24.3969, 124.1531),
    "フサキビーチリゾート": (24.3667, 124.1389),
    "グランヴィリオリゾート": (24.4086, 124.1639),
    "アートホテル": (24.3378, 124.1561),
    "石垣シーサイドホテル": (24.3542, 124.1689),
    "川平ベイリゾート": (24.4426, 124.1456)  # 川平湾近く
}

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
print(f"- 車両数: {len(vehicle_ids)}台")

# 3. 最適化を実行（3つの戦略でテスト）
strategies = ["efficiency", "safety", "balanced"]

for strategy in strategies:
    print(f"\n\n=== {strategy.upper()}戦略での最適化 ===")
    
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
            "max_pickup_time_minutes": 120,
            "buffer_time_minutes": 10,
            "weather_consideration": False
        },
        "optimization_strategy": strategy,
        "departure_time": "09:00:00"
    }
    
    response = requests.post(f"{base_url}/optimize/route", json=optimization_data)
    if response.status_code == 200:
        job = response.json()
        job_id = job["job_id"]
        print(f"最適化ジョブ開始: {job_id}")
        
        # 結果を待機
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
            
            # 各車両の詳細
            for i, route in enumerate(result['routes']):
                print(f"\n車両{i+1} ({route['vehicle_name']}):")
                print(f"  乗客数: {len(route['assigned_guests'])}名")
                print(f"  走行距離: {route['total_distance_km']} km")
                print(f"  所要時間: {route['total_duration_minutes']} 分")
                print(f"  車両使用率: {route['vehicle_utilization']*100:.1f}%")
                
                # ピックアップ順序
                print("  ピックアップ順序:")
                for j, segment in enumerate(route['route_segments']):
                    if segment['guest_id']:
                        guest = next((g for g in guests_data if any(guest_ids[k] == segment['guest_id'] for k, g in enumerate(guests_data))), None)
                        guest_name = guest['name'] if guest else "不明"
                        print(f"    {j}. {segment['from_location']['name']} → {segment['to_location']['name']}")
                        print(f"       {segment['departure_time']} 発 → {segment['arrival_time']} 着")
                        print(f"       ゲスト: {guest_name}")
            
            # 結果を保存
            filename = f"complex_result_{strategy}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 結果を{filename}に保存しました")

# 4. クリーンアップ
print("\n\nクリーンアップ中...")
for vehicle_id in vehicle_ids:
    requests.delete(f"{base_url}/vehicles/{vehicle_id}")
for guest_id in guest_ids:
    requests.delete(f"{base_url}/guests/{guest_id}")
print("✅ クリーンアップ完了")