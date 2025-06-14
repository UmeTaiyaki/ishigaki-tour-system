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

logger = logging.getLogger(__name__)


class RouteOptimizer:
    """ルート最適化クラス"""
    
    def __init__(self):
        self.distance_calculator = DistanceCalculator()
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
            # データ準備
            data = self._prepare_data(request, guests, vehicles)
            
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
    
    def _prepare_data(self, 
                      request: OptimizationRequest,
                      guests: List[Guest],
                      vehicles: List[Vehicle]) -> Dict:
        """最適化用のデータを準備"""
        
        # 位置リストを作成（デポ + ゲストのホテル + 目的地）
        locations = []
        location_names = []
        
        # デポ（車両基地）
        depot_location = (24.3448, 124.1572)  # 石垣市街地
        locations.append(depot_location)
        location_names.append("Depot")
        
        # ゲストのピックアップ地点
        for guest in guests:
            locations.append((
                guest.pickup_location.lat,
                guest.pickup_location.lng
            ))
            location_names.append(guest.hotel_name)
        
        # 目的地（最後に追加）
        locations.append((
            request.destination.lat,
            request.destination.lng
        ))
        location_names.append(request.destination.name)
        
        # 距離行列と時間行列を作成
        distance_matrix = self.distance_calculator.create_distance_matrix(locations)
        time_matrix = self.distance_calculator.create_time_matrix(distance_matrix)
        
        # 目的地への強制的なルーティングを設定
        destination_index = len(locations) - 1
        
        # 需要（各ゲストの人数）
        demands = [0]  # デポは0
        for guest in guests:
            demands.append(guest.total_passengers)
        demands.append(0)  # 目的地は0
        
        # 車両容量
        vehicle_capacities = [v.total_capacity for v in vehicles]
        
        # 時間窓（希望ピックアップ時間）
        time_windows = self._create_time_windows(request, guests)
        
        data = {
            'distance_matrix': distance_matrix.tolist(),
            'time_matrix': time_matrix.tolist(),
            'demands': demands,
            'vehicle_capacities': vehicle_capacities,
            'num_vehicles': len(vehicles),
            'depot': 0,
            'destination': destination_index,
            'time_windows': time_windows,
            'location_names': location_names,
            'locations': locations,
            'guests': guests,
            'vehicles': vehicles,
            'num_guests': len(guests)
        }
        
        return data
    
    def _create_time_windows(self, 
                            request: OptimizationRequest,
                            guests: List[Guest]) -> List[Tuple[int, int]]:
        """時間窓を作成（分単位）"""
        # 基準時刻（朝6時）からの経過分数で表現
        base_time = datetime.combine(datetime.today(), time(6, 0))
        departure_datetime = datetime.combine(
            datetime.today(), 
            request.departure_time
        )
        
        time_windows = []
        
        # デポ（いつでもOK）
        time_windows.append((0, 240))  # 6:00-10:00
        
        # ゲストのピックアップ時間窓
        for guest in guests:
            if guest.preferred_time_window:
                start_datetime = datetime.combine(
                    datetime.today(),
                    guest.preferred_time_window.start
                )
                end_datetime = datetime.combine(
                    datetime.today(),
                    guest.preferred_time_window.end
                )
                
                start_minutes = int((start_datetime - base_time).total_seconds() / 60)
                end_minutes = int((end_datetime - base_time).total_seconds() / 60)
                
                time_windows.append((start_minutes, end_minutes))
            else:
                # デフォルト: 出発時刻の90分前から30分前
                default_start = departure_datetime - timedelta(minutes=90)
                default_end = departure_datetime - timedelta(minutes=30)
                
                start_minutes = int((default_start - base_time).total_seconds() / 60)
                end_minutes = int((default_end - base_time).total_seconds() / 60)
                
                time_windows.append((start_minutes, end_minutes))
        
        # 目的地（すべてのゲストをピックアップ後）
        # 最小でも最後のピックアップから30分後
        dest_start = int((departure_datetime - base_time).total_seconds() / 60) - 30
        dest_end = 480  # 14:00まで
        
        time_windows.append((dest_start, dest_end))
        
        return time_windows
    
    def _solve_vrp(self, data: Dict, strategy: str) -> Optional[object]:
        """OR-Toolsで車両ルーティング問題を解く"""
        
        # ルーティングインデックスマネージャーを作成
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            data['depot']
        )
        
        # ルーティングモデルを作成
        routing = pywrapcp.RoutingModel(manager)
        
        # 距離コールバック
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(data['distance_matrix'][from_node][to_node] * 100)
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # 時間コールバック
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['time_matrix'][from_node][to_node]
        
        time_callback_index = routing.RegisterTransitCallback(time_callback)
        
        # 時間次元を追加
        routing.AddDimension(
            time_callback_index,
            60,  # 待機時間の最大値（60分）
            480,  # 車両の最大時間（8時間）
            False,  # 0から開始
            'Time'
        )
        
        # 時間窓制約を追加
        time_dimension = routing.GetDimensionOrDie('Time')
        
        # すべての場所に時間窓を設定
        for location_idx in range(1, len(data['time_windows'])):
            index = manager.NodeToIndex(location_idx)
            time_window = data['time_windows'][location_idx]
            time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
        
        # 重要：すべてのゲストを目的地より前に訪問する制約
        destination_index = data['destination']
        dest_node_index = manager.NodeToIndex(destination_index)
        
        # 各ゲストは目的地より前に訪問される必要がある
        for guest_idx in range(1, data['num_guests'] + 1):
            guest_node_index = manager.NodeToIndex(guest_idx)
            # ゲストのピックアップ時刻 < 目的地到着時刻
            routing.solver().Add(
                time_dimension.CumulVar(guest_node_index) < 
                time_dimension.CumulVar(dest_node_index)
            )
        
        # すべてのゲストを必ずピックアップする
        for guest_idx in range(1, data['num_guests'] + 1):
            routing.AddDisjunction([manager.NodeToIndex(guest_idx)], 100000)
        
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
        
        # 検索パラメータ
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = self.solution_strategies.get(
            strategy, 
            self.solution_strategies['balanced']
        )
        search_parameters.time_limit.seconds = 30
        search_parameters.log_search = False
        
        # 大規模問題用の追加設定
        if len(data['distance_matrix']) > 20:
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            search_parameters.time_limit.seconds = 60
        
        # 問題を解く
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            logger.info(f"Solution found! Status: {routing.status()}")
            self._manager = manager
            self._routing = routing
            return solution
        else:
            status = routing.status()
            logger.warning(f"No solution found. Status code: {status}")
            return None
    
    def _format_solution(self, 
                        data: Dict, 
                        solution: object,
                        request: OptimizationRequest,
                        guests: List[Guest],
                        vehicles: List[Vehicle]) -> OptimizationResult:
        """解を整形して結果オブジェクトを作成"""
        
        routes = []
        total_distance = 0
        total_time = 0
        
        base_time = datetime.combine(datetime.today(), time(6, 0))
        
        for vehicle_idx in range(data['num_vehicles']):
            vehicle = vehicles[vehicle_idx]
            route_segments = []
            assigned_guests = []
            vehicle_distance = 0
            vehicle_time = 0
            
            index = self._routing.Start(vehicle_idx)
            
            # 時間次元を取得
            time_dimension = self._routing.GetDimensionOrDie('Time')
            
            while not self._routing.IsEnd(index):
                node = self._manager.IndexToNode(index)
                next_index = solution.Value(self._routing.NextVar(index))
                
                if not self._routing.IsEnd(next_index):
                    next_node = self._manager.IndexToNode(next_index)
                    
                    # セグメント情報を作成
                    distance = data['distance_matrix'][node][next_node]
                    duration = data['time_matrix'][node][next_node]
                    
                    # 現在のノードの累積時間を取得
                    time_var = time_dimension.CumulVar(index)
                    current_time_minutes = solution.Value(time_var)
                    
                    # 次のノードの累積時間を取得
                    next_time_var = time_dimension.CumulVar(next_index)
                    next_time_minutes = solution.Value(next_time_var)
                    
                    # 時刻を計算
                    departure_time = (base_time + timedelta(minutes=current_time_minutes)).time()
                    arrival_time = (base_time + timedelta(minutes=next_time_minutes)).time()
                    
                    # ゲストの特定（目的地ではないノードの場合）
                    guest_id = None
                    if 0 < next_node < data['destination']:
                        guest_idx = next_node - 1
                        if guest_idx < len(guests):
                            guest_id = guests[guest_idx].id
                            assigned_guests.append(guest_id)
                    
                    # 実際の位置情報を取得
                    from_lat, from_lng = data['locations'][node]
                    to_lat, to_lng = data['locations'][next_node]
                    
                    segment = RouteSegment(
                        from_location=Location(
                            name=data['location_names'][node],
                            lat=from_lat,
                            lng=from_lng
                        ),
                        to_location=Location(
                            name=data['location_names'][next_node],
                            lat=to_lat,
                            lng=to_lng
                        ),
                        guest_id=guest_id,
                        distance_km=distance,
                        duration_minutes=duration,
                        arrival_time=arrival_time,
                        departure_time=departure_time
                    )
                    
                    route_segments.append(segment)
                    vehicle_distance += distance
                    vehicle_time += duration
                
                index = next_index
            
            if route_segments:  # ルートがある場合のみ追加
                # 実際に乗車している人数を計算
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
        
        return OptimizationResult(
            tour_id=f"tour_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            status="success",
            total_vehicles_used=len(routes),
            routes=routes,
            total_distance_km=round(total_distance, 2),
            total_time_minutes=total_time,
            average_efficiency_score=round(average_efficiency, 2),
            optimization_metrics={
                "solver_status": self._routing.status(),
                "total_guests": len(guests),
                "strategy": request.optimization_strategy
            },
            warnings=[],
            computation_time_seconds=0  # 後で設定
        )