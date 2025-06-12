"""
OR-Tools Vehicle Routing Problem (VRP) チュートリアル
石垣島ツアー最適化の基礎となるVRP問題の解き方を学習
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


def create_data_model():
    """問題のデータを作成"""
    data = {}
    # 距離行列（各地点間の距離）
    # 0: デポ（車両基地）
    # 1-4: ピックアップ地点（ホテル）
    data['distance_matrix'] = [
        [0, 10, 15, 20, 25],  # デポから各地点
        [10, 0, 35, 25, 30],  # 地点1から各地点
        [15, 35, 0, 30, 20],  # 地点2から各地点
        [20, 25, 30, 0, 15],  # 地点3から各地点
        [25, 30, 20, 15, 0],  # 地点4から各地点
    ]
    data['num_vehicles'] = 2  # 車両数
    data['depot'] = 0  # デポのインデックス
    return data


def print_solution(data, manager, routing, solution):
    """解を表示"""
    print(f'目的関数値: {solution.ObjectiveValue()}')
    max_route_distance = 0
    
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = f'車両 {vehicle_id} のルート:\n'
        route_distance = 0
        
        while not routing.IsEnd(index):
            plan_output += f' {manager.IndexToNode(index)} ->'
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        
        plan_output += f' {manager.IndexToNode(index)}\n'
        plan_output += f'ルートの距離: {route_distance}m\n'
        print(plan_output)
        max_route_distance = max(route_distance, max_route_distance)
    
    print(f'最大ルート距離: {max_route_distance}m')


def main():
    """メインエントリーポイント"""
    # データ作成
    data = create_data_model()
    
    # ルーティングインデックスマネージャーを作成
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']),
        data['num_vehicles'], 
        data['depot']
    )
    
    # ルーティングモデルを作成
    routing = pywrapcp.RoutingModel(manager)
    
    # 距離コールバックを作成・登録
    def distance_callback(from_index, to_index):
        """2つのノード間の距離を返す"""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    
    # アークコストを定義
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # 検索パラメータを設定
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    
    # 問題を解く
    solution = routing.SolveWithParameters(search_parameters)
    
    # 解を表示
    if solution:
        print_solution(data, manager, routing, solution)
    else:
        print('解が見つかりませんでした')


if __name__ == '__main__':
    main()