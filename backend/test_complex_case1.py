import requests
import json
from datetime import datetime, date
import time

# ベースURL
base_url = "http://localhost:8000/api/v1"

print("=== 石垣島ツアー最適化 - DB統合テスト ===\n")

# 1. ツアーを作成
print("1. ツアーを作成中...")
tour_data = {
    "tour_date": "2025-06-20",
    "activity_type": "snorkeling",
    "destination_name": "川平湾",
    "destination_lat": 24.4526,
    "destination_lng": 124.1456,
    "departure_time": "08:00:00",
    "status": "planning",
    "optimization_strategy": "balanced"
}

response = requests.post(f"{base_url}/tours/", json=tour_data)
if response.status_code == 200:
    tour = response.json()
    tour_id = tour["id"]
    print(f"✅ ツアー作成成功: {tour_id}")
else:
    print(f"❌ ツアー作成失敗: {response.text}")
    exit(1)

# 2. ゲストをツアーに追加（既存のゲストIDを使用）
print("\n2. ゲストをツアーに追加中...")
# 実際のゲストIDに置き換えてください
guest_ids = [
    "1a80cd57-9f26-45af-82bb-2bf324650c61",  # 山田花子
    "f6fbfbe2-adc2-4512-ab26-3b7868a6fd0e",  # テストゲスト1
    "0b0d62ba-d12a-40cd-bf59-c4759c7dee41"   # テストゲスト1
]

for guest_id in guest_ids:
    response = requests.post(f"{base_url}/tours/{tour_id}/participants/{guest_id}")
    if response.status_code == 200:
        print(f"✅ ゲスト {guest_id} を追加")
    else:
        print(f"❌ ゲスト追加失敗: {response.text}")

# 3. ツアー情報を確認
print("\n3. ツアー情報を確認中...")
response = requests.get(f"{base_url}/tours/{tour_id}")
if response.status_code == 200:
    tour_info = response.json()
    print(f"✅ ツアー日付: {tour_info['tour_date']}")
    print(f"   参加者数: {tour_info['total_participants']}名")
    print(f"   目的地: {tour_info['destination_name']}")
    print(f"   出発時刻: {tour_info['departure_time']}")

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
response = requests.delete(f"{base_url}/tours/{tour_id}")
if response.status_code == 200:
    print("✅ ツアー削除完了")
else:
    print(f"❌ ツアー削除失敗: {response.text}")

print("\n✅ テスト完了！")