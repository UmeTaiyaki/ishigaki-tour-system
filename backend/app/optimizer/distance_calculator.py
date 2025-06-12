"""
距離計算ユーティリティ
緯度経度から実際の距離を計算
"""

import math
from typing import List, Tuple, Dict
import numpy as np


class DistanceCalculator:
    """緯度経度ベースの距離計算クラス"""
    
    EARTH_RADIUS_KM = 6371.0  # 地球の半径（km）
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Haversine公式を使用して2点間の距離を計算（km）
        
        Args:
            lat1, lon1: 地点1の緯度経度
            lat2, lon2: 地点2の緯度経度
            
        Returns:
            距離（km）
        """
        # 度をラジアンに変換
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine公式
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = DistanceCalculator.EARTH_RADIUS_KM * c
        return round(distance, 2)
    
    @staticmethod
    def create_distance_matrix(locations: List[Tuple[float, float]]) -> np.ndarray:
        """
        位置リストから距離行列を作成
        
        Args:
            locations: [(lat, lon), ...] 形式の位置リスト
            
        Returns:
            距離行列（numpy array）
        """
        n = len(locations)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    lat1, lon1 = locations[i]
                    lat2, lon2 = locations[j]
                    matrix[i][j] = DistanceCalculator.haversine_distance(
                        lat1, lon1, lat2, lon2
                    )
        
        return matrix
    
    @staticmethod
    def create_time_matrix(distance_matrix: np.ndarray, 
                          average_speed_kmh: float = 30.0) -> np.ndarray:
        """
        距離行列から時間行列を作成（分単位）
        
        Args:
            distance_matrix: 距離行列（km）
            average_speed_kmh: 平均速度（km/h）、石垣島の道路事情を考慮
            
        Returns:
            時間行列（分）
        """
        # 時間 = 距離 / 速度 * 60（分に変換）
        time_matrix = (distance_matrix / average_speed_kmh) * 60
        return np.round(time_matrix).astype(int)


# 石垣島の主要地点サンプルデータ
ISHIGAKI_LOCATIONS = {
    "depot": (24.3448, 124.1572),  # 車両基地（市街地）
    "ANAインターコンチネンタル": (24.3969, 124.1531),
    "フサキビーチリゾート": (24.3667, 124.1389),
    "グランヴィリオリゾート": (24.4086, 124.1639),
    "アートホテル": (24.3378, 124.1561),
    "川平湾": (24.4526, 124.1456),  # 観光地
}


def demo_distance_calculation():
    """距離計算のデモ"""
    print("=== 石垣島距離計算デモ ===\n")
    
    # 位置データを準備
    location_names = list(ISHIGAKI_LOCATIONS.keys())
    locations = list(ISHIGAKI_LOCATIONS.values())
    
    # 距離行列を作成
    distance_matrix = DistanceCalculator.create_distance_matrix(locations)
    time_matrix = DistanceCalculator.create_time_matrix(distance_matrix)
    
    # 結果を表示
    print("距離行列（km）:")
    print("出発地\\到着地", end="\t")
    for name in location_names:
        print(f"{name[:8]:>10}", end="")
    print()
    
    for i, from_name in enumerate(location_names):
        print(f"{from_name[:10]:<10}", end="\t")
        for j in range(len(locations)):
            print(f"{distance_matrix[i][j]:>10.1f}", end="")
        print()
    
    print("\n時間行列（分）:")
    print("出発地\\到着地", end="\t")
    for name in location_names:
        print(f"{name[:8]:>10}", end="")
    print()
    
    for i, from_name in enumerate(location_names):
        print(f"{from_name[:10]:<10}", end="\t")
        for j in range(len(locations)):
            print(f"{time_matrix[i][j]:>10d}", end="")
        print()


if __name__ == "__main__":
    demo_distance_calculation()