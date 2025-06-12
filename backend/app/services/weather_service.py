"""
気象データサービス
Open-Meteo APIを使用して石垣島の気象情報を取得
"""

import httpx
from datetime import date, datetime
from typing import Dict, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class WeatherService:
    """気象データ取得サービス"""
    
    def __init__(self):
        self.base_url = settings.WEATHER_API_BASE_URL
        self.ishigaki_lat = 24.3448
        self.ishigaki_lon = 124.1572
        
    async def get_weather_forecast(self, target_date: date) -> Dict:
        """
        指定日の天気予報を取得
        
        Args:
            target_date: 対象日
            
        Returns:
            気象データ辞書
        """
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "latitude": self.ishigaki_lat,
                    "longitude": self.ishigaki_lon,
                    "hourly": "temperature_2m,precipitation,windspeed_10m,winddirection_10m",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
                    "timezone": "Asia/Tokyo",
                    "start_date": target_date.isoformat(),
                    "end_date": target_date.isoformat()
                }
                
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                return self._parse_weather_data(data, target_date)
                
        except httpx.HTTPError as e:
            logger.error(f"Weather API error: {e}")
            return self._get_default_weather()
        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}")
            return self._get_default_weather()
    
    async def get_marine_conditions(self, target_date: date) -> Dict:
        """
        海況データを取得（波高、風速など）
        
        Args:
            target_date: 対象日
            
        Returns:
            海況データ辞書
        """
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "latitude": self.ishigaki_lat,
                    "longitude": self.ishigaki_lon,
                    "hourly": "wave_height,wave_direction,wave_period",
                    "timezone": "Asia/Tokyo",
                    "start_date": target_date.isoformat(),
                    "end_date": target_date.isoformat()
                }
                
                response = await client.get(
                    f"{self.base_url}/marine",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_marine_data(data, target_date)
                else:
                    # マリンデータが利用できない場合は風速から推定
                    weather = await self.get_weather_forecast(target_date)
                    return self._estimate_marine_conditions(weather)
                    
        except Exception as e:
            logger.warning(f"Marine data not available: {e}")
            weather = await self.get_weather_forecast(target_date)
            return self._estimate_marine_conditions(weather)
    
    def _parse_weather_data(self, data: Dict, target_date: date) -> Dict:
        """気象データをパース"""
        try:
            daily = data.get("daily", {})
            hourly = data.get("hourly", {})
            
            # 9時のデータを取得（ツアー開始時刻）
            hour_index = 9
            
            return {
                "date": target_date.isoformat(),
                "temperature": {
                    "max": daily.get("temperature_2m_max", [25])[0],
                    "min": daily.get("temperature_2m_min", [20])[0],
                    "at_9am": hourly.get("temperature_2m", [23])[hour_index]
                },
                "precipitation": {
                    "daily_sum": daily.get("precipitation_sum", [0])[0],
                    "at_9am": hourly.get("precipitation", [0])[hour_index]
                },
                "wind": {
                    "max_speed": daily.get("windspeed_10m_max", [10])[0],
                    "speed_at_9am": hourly.get("windspeed_10m", [5])[hour_index],
                    "direction_at_9am": hourly.get("winddirection_10m", [0])[hour_index]
                },
                "conditions": self._determine_conditions(
                    daily.get("precipitation_sum", [0])[0],
                    daily.get("windspeed_10m_max", [10])[0]
                )
            }
        except Exception as e:
            logger.error(f"Error parsing weather data: {e}")
            return self._get_default_weather()
    
    def _parse_marine_data(self, data: Dict, target_date: date) -> Dict:
        """海況データをパース"""
        try:
            hourly = data.get("hourly", {})
            hour_index = 9
            
            return {
                "date": target_date.isoformat(),
                "wave_height": hourly.get("wave_height", [1.0])[hour_index],
                "wave_direction": hourly.get("wave_direction", [0])[hour_index],
                "wave_period": hourly.get("wave_period", [5])[hour_index],
                "suitable_for_marine_activities": True
            }
        except Exception:
            return self._get_default_marine_conditions()
    
    def _estimate_marine_conditions(self, weather: Dict) -> Dict:
        """風速から海況を推定"""
        wind_speed = weather.get("wind", {}).get("max_speed", 10)
        
        # 簡易的な波高推定（風速の0.1〜0.15倍）
        estimated_wave_height = wind_speed * 0.12
        
        return {
            "wave_height": round(estimated_wave_height, 1),
            "wave_direction": weather.get("wind", {}).get("direction_at_9am", 0),
            "wave_period": 5,
            "suitable_for_marine_activities": wind_speed < 15,
            "estimated": True
        }
    
    def _determine_conditions(self, precipitation: float, wind_speed: float) -> str:
        """天候条件を判定"""
        if precipitation > 10:
            return "rainy"
        elif wind_speed > 20:
            return "very_windy"
        elif wind_speed > 15:
            return "windy"
        elif precipitation > 0:
            return "partly_rainy"
        else:
            return "clear"
    
    def _get_default_weather(self) -> Dict:
        """デフォルトの天候データ"""
        return {
            "temperature": {"max": 28, "min": 23, "at_9am": 25},
            "precipitation": {"daily_sum": 0, "at_9am": 0},
            "wind": {"max_speed": 10, "speed_at_9am": 8, "direction_at_9am": 90},
            "conditions": "clear",
            "default": True
        }
    
    def _get_default_marine_conditions(self) -> Dict:
        """デフォルトの海況データ"""
        return {
            "wave_height": 1.0,
            "wave_direction": 90,
            "wave_period": 5,
            "suitable_for_marine_activities": True,
            "default": True
        }
    
    def get_safety_score(self, weather: Dict, marine: Dict, activity_type: str) -> float:
        """
        アクティビティの安全性スコアを計算（0.0〜1.0）
        
        Args:
            weather: 天候データ
            marine: 海況データ
            activity_type: アクティビティタイプ
            
        Returns:
            安全性スコア
        """
        score = 1.0
        
        # 共通の減点要素
        wind_speed = weather.get("wind", {}).get("max_speed", 0)
        precipitation = weather.get("precipitation", {}).get("daily_sum", 0)
        
        if wind_speed > 20:
            score *= 0.3
        elif wind_speed > 15:
            score *= 0.6
        elif wind_speed > 10:
            score *= 0.8
            
        if precipitation > 10:
            score *= 0.5
        elif precipitation > 5:
            score *= 0.7
        elif precipitation > 0:
            score *= 0.9
        
        # アクティビティ別の考慮
        if activity_type in ["snorkeling", "diving", "kayaking"]:
            wave_height = marine.get("wave_height", 0)
            if wave_height > 2:
                score *= 0.3
            elif wave_height > 1.5:
                score *= 0.6
            elif wave_height > 1:
                score *= 0.8
        
        return round(score, 2)  