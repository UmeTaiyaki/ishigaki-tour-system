# backend/test_simple_optimization.py
import requests
import json

base_url = "http://localhost:8000/api/v1"

# シンプルなテストデータ
optimization_data = {
    "tour_date": "2024-06-20",
    "activity_type": "snorkeling",
    "destination": {
        "name": "川平湾",
        "lat": 24.4526,
        "lng": 124.1456
    },
    "participant_ids": ["guest001", "guest002"],  # 2名だけ
    "available_vehicle_ids": ["vehicle001"],  # 1台だけ
    "optimization_strategy": "balanced",
    "departure_time": "09:00:00"
}

response = requests.post(f"{base_url}/optimize/route", json=optimization_data)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))