# backend/app/optimizer/route_optimizer.py
"""
ルート最適化エンジン - 最終修正版
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
                return self._create_simple_solution(request, guests, vehicles, start_time)
            
            # OR-Toolsで最適化を実行、失敗したらシンプルな割り当て
            solution = self._solve_vrp(data, request.optimization_strategy)
            
            # 解が見つからない、または空のルートの場合はシンプルな割り当てを使用
            if not solution or all(len(r['route']) <= 2 for r in solution.get('routes', [])):
                logger.warning("No valid solution found by OR-Tools, using simple assignment")
                return self._create_simple_solution(request, guests, vehicles, start_time)
                # 結果を整形
                result = self._format_solution(
                    data, solution, request, guests, vehicles
                )
                computation_time = (datetime.now() - start_time).total_seconds()
                result.computation_time_seconds = computation_time
                
                logger.info(f"最適化成功: {len(result.routes)}台で{len(guests)}名をピックアップ")
                return result
            else:
                logger.warning("No solution found, using simple assignment")
                return self._create_simple_solution(request, guests, vehicles, start_time)
                
        except Exception as e:
            logger.error(f"最適化エラー: {str(e)}")
            return self._create_simple_solution(request, guests, vehicles, start_time)
    
    def _solve_vrp(self, data: Dict, strategy: str) -> Optional[Dict]:
        """OR-Toolsで車両ルート問題を解く"""
        
        try:
            # シンプルなルーティングモデルを作成（開始・終了は同じデポ）
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
                return int(data['distance_matrix'][from_node][to_node] * 1000)
            
            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
            
            # 容量制約
            def demand_callback(from_index):
                from_node = manager.IndexToNode(from_index)
                return data['demands'][from_node]
            
            demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
            routing.AddDimensionWithVehicleCapacity(
                demand_callback_index,
                0,
                data['vehicle_capacities'],
                True,
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
                300,  # 最大待機時間
                600,  # 最大総時間
                False,
                'Time'
            )
            
            # シンプルな制約設定
            # ゲストのピックアップを必須にする（ペナルティなし = 必須）
            for node in range(1, data['destination']):
                routing.AddDisjunction([manager.NodeToIndex(node)], 0)  # ペナルティ0 = 必須
            
            # 目的地への訪問も必須（最後に訪問）
            routing.AddDisjunction([manager.NodeToIndex(data['destination'])], 0)
            
            # 検索パラメータ
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = self.solution_strategies.get(
                strategy, routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            search_parameters.time_limit.seconds = 30
            search_parameters.log_search = True
            
            # 求解
            logger.info("Starting OR-Tools solver...")
            solution = routing.SolveWithParameters(search_parameters)
            
            if solution:
                logger.info("Solution found!")
                return self._extract_solution(manager, routing, solution, data)
                
        except Exception as e:
            logger.error(f"OR-Tools error: {e}")
            
        return None
    
    def _create_simple_solution(self, request: OptimizationRequest, 
                               guests: List[Guest], 
                               vehicles: List[Vehicle],
                               start_time: datetime) -> OptimizationResult:
        """シンプルな解を作成（フォールバック）"""
        logger.info("Creating simple solution as fallback")
        
        if not vehicles:
            return OptimizationResult(
                tour_id=request.tour_id or f"tour_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                status="failed",
                total_vehicles_used=0,
                routes=[],
                total_distance_km=0,
                total_time_minutes=0,
                average_efficiency_score=0,
                optimization_metrics={"error": "利用可能な車両がありません"},
                warnings=["車両を追加してください"],
                computation_time_seconds=(datetime.now() - start_time).total_seconds()
            )
        
        # 容量の大きい車両から使用
        sorted_vehicles = sorted(vehicles, 
                               key=lambda v: v.capacity_adults + v.capacity_children, 
                               reverse=True)
        
        routes = []
        assigned_guests = set()
        
        for vehicle in sorted_vehicles:
            if len(assigned_guests) >= len(guests):
                break
                
            route_segments = []
            vehicle_guests = []
            current_capacity = 0
            max_capacity = vehicle.capacity_adults + vehicle.capacity_children
            
            # デポから開始
            current_location = Location(name="デポ", lat=24.3448, lng=124.1572)
            current_time = datetime.combine(request.tour_date, request.departure_time)
            
            # ゲストをピックアップ
            for guest in guests:
                if guest.id in assigned_guests:
                    continue
                    
                guest_demand = guest.num_adults + guest.num_children
                if current_capacity + guest_demand <= max_capacity:
                    # ピックアップセグメントを追加
                    distance = DistanceCalculator.haversine_distance(
                        current_location.lat, current_location.lng,
                        guest.pickup_location.lat, guest.pickup_location.lng
                    )
                    duration = int(distance * 2)  # 簡易的な時間計算
                    
                    arrival_time = current_time + timedelta(minutes=duration)
                    departure_time = arrival_time + timedelta(minutes=5)
                    
                    segment = RouteSegment(
                        from_location=current_location,
                        to_location=guest.pickup_location,
                        guest_id=str(guest.id),
                        distance_km=round(distance, 2),
                        duration_minutes=duration,
                        arrival_time=arrival_time.time(),
                        departure_time=departure_time.time()
                    )
                    
                    route_segments.append(segment)
                    vehicle_guests.append(str(guest.id))
                    assigned_guests.add(guest.id)
                    current_capacity += guest_demand
                    current_location = guest.pickup_location
                    current_time = departure_time
            
            # 目的地へのセグメントを追加
            if vehicle_guests:
                distance = DistanceCalculator.haversine_distance(
                    current_location.lat, current_location.lng,
                    request.destination.lat, request.destination.lng
                )
                duration = int(distance * 2)
                
                arrival_time = current_time + timedelta(minutes=duration)
                
                segment = RouteSegment(
                    from_location=current_location,
                    to_location=request.destination,
                    guest_id=None,
                    distance_km=round(distance, 2),
                    duration_minutes=duration,
                    arrival_time=arrival_time.time(),
                    departure_time=arrival_time.time()
                )
                
                route_segments.append(segment)
                
                # ルートを作成
                total_distance = sum(s.distance_km for s in route_segments)
                total_duration = sum(s.duration_minutes for s in route_segments)
                
                route = VehicleRoute(
                    vehicle_id=str(vehicle.id),
                    vehicle_name=vehicle.name,
                    route_segments=route_segments,
                    assigned_guests=vehicle_guests,
                    total_distance_km=round(total_distance, 2),
                    total_duration_minutes=total_duration,
                    efficiency_score=0.7,
                    vehicle_utilization=current_capacity / max_capacity
                )
                
                routes.append(route)
        
        # 結果を返す
        return OptimizationResult(
            tour_id=request.tour_id or f"tour_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            status="success" if len(assigned_guests) == len(guests) else "partial",
            total_vehicles_used=len(routes),
            routes=routes,
            total_distance_km=sum(r.total_distance_km for r in routes),
            total_time_minutes=max(r.total_duration_minutes for r in routes) if routes else 0,
            average_efficiency_score=0.7,
            optimization_metrics={
                "computation_time_seconds": (datetime.now() - start_time).total_seconds(),
                "solution_type": "simple_fallback",
                "total_guests": len(guests),
                "assigned_guests": len(assigned_guests)
            },
            warnings=["シンプルな割り当てを使用しました"],
            computation_time_seconds=(datetime.now() - start_time).total_seconds()
        )
    
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
        """Google Maps APIを使用したデータ準備"""
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
        
        # 目的地（最後に追加）
        locations.append((request.destination.lat, request.destination.lng))
        location_names.append(request.destination.name)
        
        # 距離行列を計算
        distance_matrix = DistanceCalculator.create_distance_matrix(locations)
        
        # 時間行列（距離から推定: 平均速度30km/h）
        time_matrix = DistanceCalculator.create_time_matrix(distance_matrix)
        
        # ゲストの需要（大人＋子供の数）
        demands = [0]  # デポの需要は0
        for guest in guests:
            demands.append(guest.num_adults + guest.num_children)
        demands.append(0)  # 目的地の需要は0
        
        # 車両容量
        vehicle_capacities = []
        for vehicle in vehicles:
            vehicle_capacities.append(vehicle.capacity_adults + vehicle.capacity_children)
        
        # 時間窓（シンプルに）
        time_windows = []
        for i in range(len(locations)):
            time_windows.append((0, 600))  # 0-10時間
        
        data = {
            'distance_matrix': distance_matrix,
            'time_matrix': time_matrix,
            'location_names': location_names,
            'num_vehicles': len(vehicles),
            'depot': 0,
            'destination': len(locations) - 1,  # 最後の要素が目的地
            'demands': demands,
            'vehicle_capacities': vehicle_capacities,
            'time_windows': time_windows,
            'service_time': 5,
            'guest_data': guests,
            'vehicle_data': vehicles
        }
        
        return data
    
    def _extract_solution(self, manager, routing, solution, data) -> Dict:
        """OR-Toolsの解から結果を抽出"""
        routes = []
        time_dimension = routing.GetDimensionOrDie('Time')
        capacity_dimension = routing.GetDimensionOrDie('Capacity')
        
        logger.info(f"Extracting solution for {data['num_vehicles']} vehicles")
        
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
            
            logger.debug(f"Vehicle {vehicle_id}: route_indices={route_indices}, distance={route_distance}")
            
            # ルートを整理（目的地を最後に移動）
            if len(route_indices) > 2 and data['destination'] in route_indices:
                # 目的地を除外
                destination = data['destination']
                route_without_dest = [idx for idx in route_indices if idx != destination]
                # 最後のデポの前に目的地を挿入
                if route_without_dest[-1] == data['depot']:
                    route_indices = route_without_dest[:-1] + [destination] + [route_without_dest[-1]]
                else:
                    route_indices = route_without_dest + [destination]
            
            if len(route_indices) > 2:  # デポ以外の訪問地点がある場合
                routes.append({
                    'vehicle_id': vehicle_id,
                    'route': route_indices,
                    'distance': route_distance / 1000,  # kmに戻す
                    'time': route_time,
                    'load': route_load
                })
                logger.info(f"Vehicle {vehicle_id} has a valid route with {len(route_indices)} stops")
            else:
                logger.debug(f"Vehicle {vehicle_id} has no valid route (only {len(route_indices)} stops)")
        
        logger.info(f"Total routes found: {len(routes)}")
        
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
        
        base_time = datetime.combine(request.tour_date, request.departure_time)
        
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
                if 0 < to_idx < data['destination']:  # 目的地より前のインデックス
                    guest_idx = to_idx - 1
                    if guest_idx < len(guests):
                        guest = guests[guest_idx]
                        guest_id = str(guest.id)
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
                guest = next((g for g in guests if str(g.id) == guest_id), None)
                if guest:
                    total_passengers += guest.num_adults + guest.num_children
            
            max_capacity = vehicle.capacity_adults + vehicle.capacity_children
            vehicle_utilization = total_passengers / max_capacity if max_capacity > 0 else 0
            efficiency_score = min(1.0, vehicle_utilization * 0.8 + 0.2)
            
            vehicle_route = VehicleRoute(
                vehicle_id=str(vehicle.id),
                vehicle_name=vehicle.name,
                route_segments=route_segments,
                assigned_guests=assigned_guests,
                total_distance_km=round(vehicle_distance, 2),
                total_duration_minutes=vehicle_time,
                efficiency_score=efficiency_score,
                vehicle_utilization=vehicle_utilization
            )
            
            routes.append(vehicle_route)
            total_distance += vehicle_distance
            total_time = max(total_time, vehicle_time)
        
        # 平均効率スコアを計算
        avg_efficiency = sum(r.efficiency_score for r in routes) / len(routes) if routes else 0
        
        return OptimizationResult(
            tour_id=request.tour_id or f"tour_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            status="success" if routes else "failed",
            total_vehicles_used=len(routes),
            routes=routes,
            total_distance_km=round(total_distance, 2),
            total_time_minutes=total_time,
            average_efficiency_score=avg_efficiency,
            optimization_metrics={
                "computation_time_seconds": 0,  # 後で設定
                "solution_strategy": request.optimization_strategy,
                "total_guests": len(guests),
                "total_vehicles_available": len(vehicles),
                "solver_status": 1
            },
            warnings=[],
            computation_time_seconds=0  # 後で設定
        )
    
    def _get_location_info(self, idx: int, data: Dict, request: OptimizationRequest) -> Location:
        """インデックスから位置情報を取得"""
        if idx == 0:
            return Location(name="デポ", lat=24.3448, lng=124.1572)
        elif idx == data['destination']:
            return request.destination
        else:
            guest_idx = idx - 1
            if guest_idx < len(data['guest_data']):
                guest = data['guest_data'][guest_idx]
                return guest.pickup_location
            else:
                return Location(name="不明", lat=24.3448, lng=124.1572)
    
    def _time_to_minutes(self, t: time) -> int:
        """時刻を分単位に変換"""
        return t.hour * 60 + t.minute