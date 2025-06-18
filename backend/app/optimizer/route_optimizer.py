# backend/app/optimizer/route_optimizer.py
"""
ルート最適化エンジン
OR-Toolsを使用した石垣島ツアーのルート最適化
"""

from typing import List, Dict, Tuple, Optional
import logging
from datetime import time, datetime, timedelta
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np

from app.schemas.optimization import (
    Guest, Vehicle, Location, OptimizationRequest,
    VehicleRoute, RouteSegment, OptimizationResult
)
from app.optimizer.distance_calculator import DistanceCalculator
from app.services.google_maps_service import GoogleMapsService

logger = logging.getLogger(__name__)


class RouteOptimizer:
    """ルート最適化クラス"""
    
    def __init__(self):
        self.distance_calculator = DistanceCalculator()
        self.google_maps_service = GoogleMapsService()
        self.solution_strategies = {
            'safety': routing_enums_pb2.FirstSolutionStrategy.PATH_MOST_CONSTRAINED_ARC,
            'efficiency': routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
            'balanced': routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        }
        self.weather_service = None  # 遅延初期化
        
    def optimize(self, 
                 request: OptimizationRequest,
                 guests: List[Guest],
                 vehicles: List[Vehicle]) -> OptimizationResult:
        """
        ルート最適化を実行
        
        Args:
            request: 最適化リクエスト
            guests: ゲストリスト
            vehicles: 利用可能な車両リスト
            
        Returns:
            最適化結果
        """
        start_time = datetime.now()
        
        try:
            # データ準備（Google Maps API対応版を使用）
            data = self._prepare_data_async(request, guests, vehicles)
            
            # デバッグ情報
            logger.info(f"Optimization problem size:")
            logger.info(f"  - Guests: {len(guests)}")
            logger.info(f"  - Vehicles: {len(vehicles)}")
            logger.info(f"  - Total capacity: {sum(data['vehicle_capacities'])}")
            logger.info(f"  - Total demand: {sum(data['demands'])}")
            
            # 実行可能性チェック
            if sum(data['demands']) > sum(data['vehicle_capacities']):
                logger.warning("Total demand exceeds total capacity!")
                return OptimizationResult(
                    tour_id=f"tour_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    status="failed",
                    total_vehicles_used=0,
                    routes=[],
                    total_distance_km=0,
                    total_time_minutes=0,
                    average_efficiency_score=0,
                    optimization_metrics={"error": "需要が車両容量を超えています"},
                    warnings=["車両を追加するか、ゲスト数を減らしてください"],
                    computation_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # OR-Toolsで最適化
            solution = self._solve_vrp(data, request.optimization_strategy)
            
            if solution:
                # 結果を整形
                result = self._format_solution(
                    data, solution, request, guests, vehicles
                )
                computation_time = (datetime.now() - start_time).total_seconds()
                result.computation_time_seconds = computation_time
                
                logger.info(f"最適化成功: {len(vehicles)}台で{len(guests)}名をピックアップ")
                return result
            else:
                return OptimizationResult(
                    tour_id=f"tour_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    status="failed",
                    total_vehicles_used=0,
                    routes=[],
                    total_distance_km=0,
                    total_time_minutes=0,
                    average_efficiency_score=0,
                    optimization_metrics={"error": "解が見つかりませんでした"},
                    warnings=["最適化に失敗しました"],
                    computation_time_seconds=(datetime.now() - start_time).total_seconds()
                )
                
        except Exception as e:
            logger.error(f"最適化エラー: {str(e)}")
            raise
    
    def _prepare_data_async(self, 
                      request: OptimizationRequest,
                      guests: List[Guest],
                      vehicles: List[Vehicle]) -> Dict:
        """非同期版のデータ準備（同期的に呼び出し）"""
        import asyncio
        
        # 新しいイベントループを作成して実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._prepare_data_with_google_maps(request, guests, vehicles)
            )
        finally:
            loop.close()
    
    async def _prepare_data_with_google_maps(
        self,
        request: OptimizationRequest,
        guests: List[Guest],
        vehicles: List[Vehicle]
    ) -> Dict:
        """Google Maps APIを使用してデータを準備"""
        
        # 位置情報を抽出
        locations = []
        location_names = []
        
        # デポ（仮想的な開始地点）
        depot_location = (24.3448, 124.1572)  # 石垣島の中心
        locations.append(depot_location)
        location_names.append("デポ")
        
        # ゲストのピックアップ地点
        for guest in guests:
            locations.append((guest.pickup_location.lat, guest.pickup_location.lng))
            location_names.append(guest.pickup_location.name)
        
        # 目的地
        locations.append((request.destination.lat, request.destination.lng))
        location_names.append(request.destination.name)
        
        # Google Maps APIまたはHaversine距離で距離行列を取得
        if self.google_maps_service.enabled:
            logger.info("Using Google Maps API for distance calculation")
            matrix_result = await self.google_maps_service.get_distance_matrix(
                origins=locations,
                destinations=locations,
                departure_time=datetime.combine(
                    request.tour_date,
                    request.departure_time
                )
            )
            
            distance_matrix = matrix_result['distance_matrix'].tolist()
            time_matrix = matrix_result['duration_matrix'].astype(int).tolist()
            
            logger.info(f"Distance matrix calculation method: {matrix_result['status']}")
        else:
            # フォールバック: 既存のHaversine距離計算
            logger.info("Using Haversine distance calculation (fallback)")
            distance_matrix = self.distance_calculator.calculate_distance_matrix(locations)
            time_matrix = [[int(d * 2) for d in row] for row in distance_matrix]
        
        # ゲストの需要（大人＋子供の数）
        demands = [0]  # デポの需要は0
        for guest in guests:
            demands.append(guest.num_adults + guest.num_children)
        demands.append(0)  # 目的地の需要は0
        
        # 車両容量
        vehicle_capacities = []
        for vehicle in vehicles:
            vehicle_capacities.append(vehicle.capacity_adults + vehicle.capacity_children)
        
        # 時間窓の設定
        time_windows = []
        base_time = 6 * 60  # 6:00 AMを基準（分単位）
        
        # デポの時間窓（広い範囲）
        time_windows.append((base_time, base_time + 4 * 60))
        
        # ゲストの時間窓（安全な処理）
        for guest in guests:
            try:
                if guest.preferred_time_window is not None:
                    # TimeWindowオブジェクトの場合
                    if hasattr(guest.preferred_time_window, 'start_time') and hasattr(guest.preferred_time_window, 'end_time'):
                        start_minutes = self._time_to_minutes(guest.preferred_time_window.start_time) - base_time
                        end_minutes = self._time_to_minutes(guest.preferred_time_window.end_time) - base_time
                        time_windows.append((start_minutes, end_minutes))
                    # 辞書型の場合
                    elif isinstance(guest.preferred_time_window, dict):
                        start_time = guest.preferred_time_window.get('start_time')
                        end_time = guest.preferred_time_window.get('end_time')
                        if start_time and end_time:
                            # 文字列の場合は変換
                            if isinstance(start_time, str):
                                start_time = datetime.strptime(start_time, "%H:%M:%S").time()
                            if isinstance(end_time, str):
                                end_time = datetime.strptime(end_time, "%H:%M:%S").time()
                            
                            start_minutes = self._time_to_minutes(start_time) - base_time
                            end_minutes = self._time_to_minutes(end_time) - base_time
                            time_windows.append((start_minutes, end_minutes))
                        else:
                            time_windows.append((60, 180))  # デフォルト
                    else:
                        time_windows.append((60, 180))  # デフォルト
                else:
                    # デフォルトの時間窓（7:00-9:00）
                    time_windows.append((60, 180))
            except Exception as e:
                logger.warning(f"Error processing time window for guest {guest.id}: {e}")
                time_windows.append((60, 180))  # エラー時はデフォルト
        
        # 目的地の時間窓（到着希望時刻周辺）
        departure_minutes = self._time_to_minutes(request.departure_time) - base_time
        time_windows.append((departure_minutes - 30, departure_minutes + 30))
        
        data = {
            'distance_matrix': distance_matrix,
            'time_matrix': time_matrix,
            'location_names': location_names,
            'num_vehicles': len(vehicles),
            'depot': 0,
            'destination': len(locations) - 1,
            'demands': demands,
            'vehicle_capacities': vehicle_capacities,
            'time_windows': time_windows,
            'service_time': 5,  # 各地点でのサービス時間（分）
            'guest_data': guests,
            'vehicle_data': vehicles
        }
        
        return data
    
    def _prepare_data(self, 
                      request: OptimizationRequest,
                      guests: List[Guest],
                      vehicles: List[Vehicle]) -> Dict:
        """データ準備（既存のHaversine版 - 後方互換性のため残す）"""
        # 位置情報を抽出
        locations = []
        location_names = []
        
        # デポ（仮想的な開始地点）
        depot_location = (24.3448, 124.1572)  # 石垣島の中心
        locations.append(depot_location)
        location_names.append("デポ")
        
        # ゲストのピックアップ地点
        for guest in guests:
            locations.append((guest.pickup_location.lat, guest.pickup_location.lng))
            location_names.append(guest.pickup_location.name)
        
        # 目的地
        locations.append((request.destination.lat, request.destination.lng))
        location_names.append(request.destination.name)
        
        # 距離行列を計算
        distance_matrix = self.distance_calculator.calculate_distance_matrix(locations)
        
        # 時間行列（距離から推定: 平均速度30km/h）
        time_matrix = [[int(d * 2) for d in row] for row in distance_matrix]
        
        # ゲストの需要（大人＋子供の数）
        demands = [0]  # デポの需要は0
        for guest in guests:
            demands.append(guest.num_adults + guest.num_children)
        demands.append(0)  # 目的地の需要は0
        
        # 車両容量
        vehicle_capacities = []
        for vehicle in vehicles:
            vehicle_capacities.append(vehicle.capacity_adults + vehicle.capacity_children)
        
        # 時間窓の設定
        time_windows = []
        base_time = 6 * 60  # 6:00 AMを基準（分単位）
        
        # デポの時間窓（広い範囲）
        time_windows.append((base_time, base_time + 4 * 60))
        
        # ゲストの時間窓（安全な処理）
        for guest in guests:
            try:
                if guest.preferred_time_window is not None:
                    # TimeWindowオブジェクトの場合
                    if hasattr(guest.preferred_time_window, 'start_time') and hasattr(guest.preferred_time_window, 'end_time'):
                        start_minutes = self._time_to_minutes(guest.preferred_time_window.start_time) - base_time
                        end_minutes = self._time_to_minutes(guest.preferred_time_window.end_time) - base_time
                        time_windows.append((start_minutes, end_minutes))
                    # 辞書型の場合
                    elif isinstance(guest.preferred_time_window, dict):
                        start_time = guest.preferred_time_window.get('start_time')
                        end_time = guest.preferred_time_window.get('end_time')
                        if start_time and end_time:
                            # 文字列の場合は変換
                            if isinstance(start_time, str):
                                start_time = datetime.strptime(start_time, "%H:%M:%S").time()
                            if isinstance(end_time, str):
                                end_time = datetime.strptime(end_time, "%H:%M:%S").time()
                            
                            start_minutes = self._time_to_minutes(start_time) - base_time
                            end_minutes = self._time_to_minutes(end_time) - base_time
                            time_windows.append((start_minutes, end_minutes))
                        else:
                            time_windows.append((60, 180))  # デフォルト
                    else:
                        time_windows.append((60, 180))  # デフォルト
                else:
                    # デフォルトの時間窓（7:00-9:00）
                    time_windows.append((60, 180))
            except Exception as e:
                logger.warning(f"Error processing time window for guest {guest.id}: {e}")
                time_windows.append((60, 180))  # エラー時はデフォルト
        
        # 目的地の時間窓（到着希望時刻周辺）
        departure_minutes = self._time_to_minutes(request.departure_time) - base_time
        time_windows.append((departure_minutes - 30, departure_minutes + 30))
        
        data = {
            'distance_matrix': distance_matrix,
            'time_matrix': time_matrix,
            'location_names': location_names,
            'num_vehicles': len(vehicles),
            'depot': 0,
            'destination': len(locations) - 1,
            'demands': demands,
            'vehicle_capacities': vehicle_capacities,
            'time_windows': time_windows,
            'service_time': 5,  # 各地点でのサービス時間（分）
            'guest_data': guests,
            'vehicle_data': vehicles
        }
        
        return data
    
    def _solve_vrp(self, data: Dict, strategy: str) -> Optional[Dict]:
        """OR-Toolsで車両ルート問題を解く"""
        
        # ルーティングモデルを作成
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            data['depot']
        )
        
        routing = pywrapcp.RoutingModel(manager)
        
        # 距離のコールバック
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(data['distance_matrix'][from_node][to_node] * 1000)  # メートル単位に変換
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # 容量制約
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],
            True,  # start cumul to zero
            'Capacity'
        )
        
        # 時間制約
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            travel_time = data['time_matrix'][from_node][to_node]
            service_time = data['service_time'] if from_node != data['depot'] else 0
            return travel_time + service_time
        
        time_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.AddDimension(
            time_callback_index,
            30,  # 最大待機時間（分）
            480,  # 最大総時間（8時間）
            False,  # 開始時刻を0にしない
            'Time'
        )
        
        time_dimension = routing.GetDimensionOrDie('Time')
        
        # 時間窓を設定
        for location_idx, time_window in enumerate(data['time_windows']):
            if location_idx == data['depot']:
                continue
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
        
        # 各車両の開始・終了時刻を設定
        for vehicle_id in range(data['num_vehicles']):
            start_index = routing.Start(vehicle_id)
            end_index = routing.End(vehicle_id)
            time_dimension.CumulVar(start_index).SetRange(
                data['time_windows'][0][0], data['time_windows'][0][1]
            )
            # 終了時刻は自由
            time_dimension.CumulVar(end_index).SetRange(0, 480)
        
        # 最終目的地への到着を強制
        for vehicle_id in range(data['num_vehicles']):
            routing.SetFixedCostOfVehicle(10000, vehicle_id)
            end_index = routing.End(vehicle_id)
            # 最終目的地をすべての車両の終点として設定
            routing.AddDisjunction([manager.NodeToIndex(data['destination'])], 10000)
        
        # 検索パラメータ
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = self.solution_strategies.get(
            strategy, routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.time_limit.seconds = 30  # 30秒のタイムリミット
        
        # 求解
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            return self._extract_solution(manager, routing, solution, data)
        
        return None
    
    def _extract_solution(self, manager, routing, solution, data) -> Dict:
        """OR-Toolsの解から結果を抽出"""
        routes = []
        time_dimension = routing.GetDimensionOrDie('Time')
        capacity_dimension = routing.GetDimensionOrDie('Capacity')
        
        for vehicle_id in range(data['num_vehicles']):
            index = routing.Start(vehicle_id)
            route_indices = []
            route_distance = 0
            route_time = 0
            route_load = 0
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route_indices.append(node_index)
                
                # 時間情報を取得
                time_var = time_dimension.CumulVar(index)
                route_time = solution.Value(time_var)
                
                # 容量情報を取得
                load_var = capacity_dimension.CumulVar(index)
                route_load = solution.Value(load_var)
                
                # 次のノードへ
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_id
                )
            
            # 最終ノード（デポに戻る）を追加
            node_index = manager.IndexToNode(index)
            route_indices.append(node_index)
            
            if len(route_indices) > 2:  # デポ以外の訪問地点がある場合
                routes.append({
                    'vehicle_id': vehicle_id,
                    'route': route_indices,
                    'distance': route_distance / 1000,  # kmに戻す
                    'time': route_time,
                    'load': route_load
                })
        
        return {
            'routes': routes,
            'total_distance': sum(r['distance'] for r in routes),
            'total_time': max(r['time'] for r in routes) if routes else 0
        }
    
    def _format_solution(self, data: Dict, solution: Dict, 
                        request: OptimizationRequest,
                        guests: List[Guest], 
                        vehicles: List[Vehicle]) -> OptimizationResult:
        """解を最終的な結果形式に整形"""
        routes = []
        total_distance = 0
        total_time = 0
        
        base_time = datetime.combine(request.tour_date, time(6, 0))
        
        for route_data in solution['routes']:
            vehicle_id = route_data['vehicle_id']
            vehicle = vehicles[vehicle_id]
            
            route_segments = []
            assigned_guests = []
            vehicle_distance = 0
            vehicle_time = 0
            
            route = route_data['route']
            
            for i in range(len(route) - 1):
                from_idx = route[i]
                to_idx = route[i + 1]
                
                # 位置情報を取得
                from_location = self._get_location_info(from_idx, data, request)
                to_location = self._get_location_info(to_idx, data, request)
                
                # ゲストIDを特定
                guest_id = None
                if 0 < to_idx < len(data['location_names']) - 1:
                    guest_idx = to_idx - 1
                    if guest_idx < len(guests):
                        guest = guests[guest_idx]
                        guest_id = guest.id
                        assigned_guests.append(guest_id)
                
                # 時刻計算
                segment_distance = data['distance_matrix'][from_idx][to_idx]
                segment_duration = data['time_matrix'][from_idx][to_idx]
                
                arrival_time = base_time + timedelta(minutes=vehicle_time + segment_duration)
                departure_time = arrival_time + timedelta(minutes=data['service_time'])
                
                vehicle_distance += segment_distance
                vehicle_time += segment_duration + data['service_time']
                
                segment = RouteSegment(
                    from_location=from_location,
                    to_location=to_location,
                    guest_id=guest_id,
                    distance_km=round(segment_distance, 2),
                    duration_minutes=segment_duration,
                    arrival_time=arrival_time.time(),
                    departure_time=departure_time.time()
                )
                
                route_segments.append(segment)
            
            # 車両利用率を計算
            total_passengers = 0
            for guest_id in assigned_guests:
                guest = next((g for g in guests if g.id == guest_id), None)
                if guest:
                    total_passengers += guest.total_passengers
            
            vehicle_utilization = total_passengers / vehicle.total_capacity if vehicle.total_capacity > 0 else 0
            efficiency_score = min(1.0, vehicle_utilization * 0.8 + 0.2)
            
            vehicle_route = VehicleRoute(
                vehicle_id=vehicle.id,
                vehicle_name=vehicle.name,
                route_segments=route_segments,
                assigned_guests=assigned_guests,
                total_distance_km=round(vehicle_distance, 2),
                total_duration_minutes=vehicle_time,
                efficiency_score=round(efficiency_score, 2),
                vehicle_utilization=round(vehicle_utilization, 2)
            )
            
            routes.append(vehicle_route)
            total_distance += vehicle_distance
            total_time = max(total_time, vehicle_time)
        
        # 平均効率性スコア
        average_efficiency = sum(r.efficiency_score for r in routes) / len(routes) if routes else 0
        
        # 警告メッセージの生成
        warnings = []
        if average_efficiency < 0.7:
            warnings.append("車両の利用効率が低くなっています。車両数を減らすことを検討してください。")
        if total_time > 360:  # 6時間以上
            warnings.append("総所要時間が長くなっています。ルートの見直しを検討してください。")
        
        return OptimizationResult(
            tour_id=f"tour_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            status="success",
            total_vehicles_used=len(routes),
            routes=routes,
            total_distance_km=round(total_distance, 2),
            total_time_minutes=total_time,
            average_efficiency_score=round(average_efficiency, 2),
            optimization_metrics={
                "solver_status": "completed",
                "total_guests": len(guests),
                "strategy": request.optimization_strategy,
                "computation_method": "google_maps" if self.google_maps_service.enabled else "haversine"
            },
            warnings=warnings,
            computation_time_seconds=0  # 後で設定される
        )
    
    def _get_location_info(self, index: int, data: Dict, 
                          request: OptimizationRequest) -> Location:
        """インデックスから位置情報を取得"""
        if index == 0:
            # デポ
            return Location(name="デポ", lat=24.3448, lng=124.1572)
        elif index == len(data['location_names']) - 1:
            # 目的地
            return request.destination
        else:
            # ゲストのピックアップ地点
            guest_idx = index - 1
            if guest_idx < len(data['guest_data']):
                guest = data['guest_data'][guest_idx]
                return guest.pickup_location
            else:
                return Location(name=f"Unknown {index}", lat=0, lng=0)
    
    def _time_to_minutes(self, t: time) -> int:
        """時刻を分に変換"""
        return t.hour * 60 + t.minute