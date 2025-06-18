# backend/app/services/google_maps_service.py
import googlemaps
from typing import List, Tuple, Dict, Optional
import numpy as np
from datetime import datetime
import logging
from math import radians, sin, cos, sqrt, atan2

logger = logging.getLogger(__name__)

class GoogleMapsService:
    def __init__(self, api_key: Optional[str] = None):
        """Google Maps クライアントを初期化"""
        from app.core.config import settings
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        
        if self.api_key and self.api_key != "your-google-maps-api-key":
            self.client = googlemaps.Client(key=self.api_key)
            self.enabled = True
            logger.info("Google Maps API enabled")
        else:
            self.client = None
            self.enabled = False
            logger.warning("Google Maps API key not configured, using fallback calculations")
    
    async def get_distance_matrix(
        self,
        origins: List[Tuple[float, float]],
        destinations: List[Tuple[float, float]],
        departure_time: datetime = None,
        mode: str = "driving"
    ) -> Dict[str, np.ndarray]:
        """
        Google Maps Distance Matrix APIを使用して実際の道路距離と時間を取得
        """
        if not self.enabled:
            # フォールバック: Haversine距離を使用
            return self._calculate_haversine_matrix(origins, destinations)
        
        try:
            # 位置情報を文字列形式に変換
            origin_strs = [f"{lat},{lng}" for lat, lng in origins]
            dest_strs = [f"{lat},{lng}" for lat, lng in destinations]
            
            # API呼び出し
            result = self.client.distance_matrix(
                origins=origin_strs,
                destinations=dest_strs,
                mode=mode,
                departure_time=departure_time or datetime.now(),
                traffic_model="best_guess" if mode == "driving" else None,
                units="metric"
            )
            
            # 結果を行列形式に変換
            n_origins = len(origins)
            n_dests = len(destinations)
            
            distance_matrix = np.zeros((n_origins, n_dests))
            duration_matrix = np.zeros((n_origins, n_dests))
            
            for i, row in enumerate(result['rows']):
                for j, element in enumerate(row['elements']):
                    if element['status'] == 'OK':
                        distance_matrix[i][j] = element['distance']['value'] / 1000  # km
                        duration_matrix[i][j] = element['duration']['value'] / 60    # 分
                    else:
                        # エラーの場合はHaversine距離で代替
                        distance_matrix[i][j] = self._haversine_distance(
                            origins[i], destinations[j]
                        )
                        duration_matrix[i][j] = distance_matrix[i][j] * 2  # 推定: 30km/h
            
            return {
                'distance_matrix': distance_matrix,
                'duration_matrix': duration_matrix,
                'status': 'google_maps'
            }
            
        except Exception as e:
            logger.error(f"Google Maps API error: {e}")
            # エラー時はHaversine距離にフォールバック
            return self._calculate_haversine_matrix(origins, destinations)
    
    async def get_route_details(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        waypoints: List[Tuple[float, float]] = None,
        optimize_waypoints: bool = True
    ) -> Optional[Dict]:
        """
        詳細なルート情報を取得（経路の最適化も可能）
        """
        if not self.enabled:
            return None
        
        try:
            waypoint_strs = None
            if waypoints:
                waypoint_strs = [f"{lat},{lng}" for lat, lng in waypoints]
            
            result = self.client.directions(
                origin=f"{origin[0]},{origin[1]}",
                destination=f"{destination[0]},{destination[1]}",
                waypoints=waypoint_strs,
                optimize_waypoints=optimize_waypoints,
                mode="driving",
                departure_time=datetime.now(),
                alternatives=False
            )
            
            if result:
                route = result[0]
                
                # 経路情報を抽出
                legs_info = []
                for leg in route['legs']:
                    legs_info.append({
                        'start_address': leg['start_address'],
                        'end_address': leg['end_address'],
                        'distance': leg['distance']['value'] / 1000,  # km
                        'duration': leg['duration']['value'] / 60,    # 分
                        'steps': len(leg['steps'])
                    })
                
                return {
                    'total_distance': sum(leg['distance'] for leg in legs_info),
                    'total_duration': sum(leg['duration'] for leg in legs_info),
                    'legs': legs_info,
                    'polyline': route['overview_polyline']['points'],
                    'waypoint_order': route.get('waypoint_order', []),
                    'bounds': route['bounds']
                }
            
        except Exception as e:
            logger.error(f"Google Directions API error: {e}")
        
        return None
    
    def _haversine_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Haversine公式で距離を計算（フォールバック用）"""
        R = 6371  # 地球の半径（km）
        lat1, lon1 = radians(coord1[0]), radians(coord1[1])
        lat2, lon2 = radians(coord2[0]), radians(coord2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def _calculate_haversine_matrix(
        self, 
        origins: List[Tuple[float, float]], 
        destinations: List[Tuple[float, float]]
    ) -> Dict[str, np.ndarray]:
        """Haversine距離行列を計算"""
        n_origins = len(origins)
        n_dests = len(destinations)
        
        distance_matrix = np.zeros((n_origins, n_dests))
        duration_matrix = np.zeros((n_origins, n_dests))
        
        for i, origin in enumerate(origins):
            for j, dest in enumerate(destinations):
                distance = self._haversine_distance(origin, dest)
                distance_matrix[i][j] = distance
                # 石垣島の平均速度30km/hと仮定
                duration_matrix[i][j] = (distance / 30) * 60  # 分
        
        return {
            'distance_matrix': distance_matrix,
            'duration_matrix': duration_matrix,
            'status': 'haversine_fallback'
        }