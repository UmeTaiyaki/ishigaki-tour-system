# backend/app/services/learning_service.py
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta, date
from collections import Counter, defaultdict
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json
import logging

from app.models.route_adjustment import RouteAdjustment, AdjustmentType
from app.models.tour import Tour
from app.models.guest import Guest
from app.models.optimized_route import OptimizedRoute

logger = logging.getLogger(__name__)


class LearningService:
    def __init__(self, db: Session):
        self.db = db
    
    async def analyze_adjustment_patterns(self, days: int = 90) -> Dict:
        """過去の調整パターンを分析して学習"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 調整データを取得
        adjustments = self.db.query(RouteAdjustment).filter(
            RouteAdjustment.adjusted_at >= cutoff_date
        ).all()
        
        if not adjustments:
            return {
                "status": "no_data",
                "message": "分析に必要な調整データがありません",
                "recommendations": []
            }
        
        analysis_result = {
            "period": {
                "start": cutoff_date.date().isoformat(),
                "end": date.today().isoformat(),
                "total_adjustments": len(adjustments)
            },
            "patterns": {
                "frequent_swaps": self._analyze_guest_swaps(adjustments),
                "time_patterns": self._analyze_time_patterns(adjustments),
                "hotel_patterns": self._analyze_hotel_patterns(adjustments),
                "distance_impact": self._analyze_distance_impact(adjustments),
                "common_reasons": self._analyze_adjustment_reasons(adjustments)
            },
            "recommendations": [],
            "learning_rules": []
        }
        
        # 推奨事項と学習ルールを生成
        analysis_result["recommendations"] = self._generate_recommendations(
            analysis_result["patterns"]
        )
        analysis_result["learning_rules"] = self._generate_learning_rules(
            analysis_result["patterns"]
        )
        
        return analysis_result
    
    def _analyze_guest_swaps(self, adjustments: List[RouteAdjustment]) -> List[Dict]:
        """頻繁に入れ替えられるゲストのペアを分析"""
        swap_pairs = []
        
        for adj in adjustments:
            if adj.adjustment_type != AdjustmentType.reorder:
                continue
                
            original = adj.original_data.get('guest_order', [])
            adjusted = adj.adjusted_data.get('guest_order', [])
            
            # 入れ替えペアを特定
            for i in range(len(original)):
                if i < len(adjusted) and original[i] != adjusted[i]:
                    # 入れ替え相手を探す
                    try:
                        swap_idx = adjusted.index(original[i])
                        if swap_idx != i:
                            pair = tuple(sorted([original[i], adjusted[i]]))
                            swap_pairs.append(pair)
                    except ValueError:
                        continue
        
        # 頻度分析
        swap_counts = Counter(swap_pairs)
        
        results = []
        for (guest1_id, guest2_id), count in swap_counts.most_common(10):
            if count >= 2:  # 2回以上の入れ替えがあったペア
                # ゲスト情報を取得
                guest1 = self.db.query(Guest).filter(Guest.id == guest1_id).first()
                guest2 = self.db.query(Guest).filter(Guest.id == guest2_id).first()
                
                if guest1 and guest2:
                    results.append({
                        "guest_pair": {
                            "guest1": {
                                "id": str(guest1.id),
                                "name": guest1.name,
                                "hotel": guest1.hotel_name
                            },
                            "guest2": {
                                "id": str(guest2.id),
                                "name": guest2.name,
                                "hotel": guest2.hotel_name
                            }
                        },
                        "frequency": count,
                        "recommendation": f"{guest1.name}と{guest2.name}は同じ車両に割り当てない方が良い可能性があります"
                    })
        
        return results
    
    def _analyze_time_patterns(self, adjustments: List[RouteAdjustment]) -> Dict:
        """時間帯別の調整パターンを分析"""
        time_adjustments = defaultdict(list)
        
        for adj in adjustments:
            if 'pickup_times' not in adj.original_data:
                continue
            
            # 調整されたピックアップ時間を分析
            original_times = adj.original_data.get('pickup_times', {})
            adjusted_times = adj.adjusted_data.get('pickup_times', {})
            
            for guest_id, original_time in original_times.items():
                if guest_id in adjusted_times:
                    adjusted_time = adjusted_times[guest_id]
                    if original_time != adjusted_time:
                        # 時間変更を記録
                        guest = self.db.query(Guest).filter(
                            Guest.id == guest_id
                        ).first()
                        if guest:
                            time_adjustments[guest.hotel_name].append({
                                'original': original_time,
                                'adjusted': adjusted_time,
                                'day_of_week': adj.adjusted_at.weekday()
                            })
        
        # パターンを分析
        patterns = {}
        for hotel, adjustments_list in time_adjustments.items():
            if len(adjustments_list) >= 3:  # 3回以上の調整があったホテル
                # DataFrameを作成して分析
                try:
                    df = pd.DataFrame(adjustments_list)
                    
                    # 最も多い調整後の時間帯
                    adjusted_hours = pd.to_datetime(df['adjusted']).dt.hour
                    if not adjusted_hours.empty:
                        preferred_hour = adjusted_hours.mode().iloc[0] if not adjusted_hours.mode().empty else None
                    else:
                        preferred_hour = None
                    
                    patterns[hotel] = {
                        "total_adjustments": len(adjustments_list),
                        "preferred_pickup_hour": int(preferred_hour) if preferred_hour is not None else None,
                        "average_delay_minutes": self._calculate_average_delay(df),
                        "weekday_pattern": self._analyze_weekday_pattern(df)
                    }
                except Exception as e:
                    logger.error(f"Error analyzing time patterns for {hotel}: {e}")
                    continue
        
        return patterns
    
    def _calculate_average_delay(self, df: pd.DataFrame) -> int:
        """平均遅延時間を計算"""
        try:
            original_times = pd.to_datetime(df['original'])
            adjusted_times = pd.to_datetime(df['adjusted'])
            delays = (adjusted_times - original_times).dt.total_seconds() / 60
            return int(delays.mean())
        except:
            return 0
    
    def _analyze_weekday_pattern(self, df: pd.DataFrame) -> Dict:
        """曜日別のパターンを分析"""
        try:
            weekday_counts = df['day_of_week'].value_counts().to_dict()
            return {
                "most_adjusted_day": max(weekday_counts, key=weekday_counts.get) if weekday_counts else None,
                "adjustments_by_day": weekday_counts
            }
        except:
            return {}
    
    def _analyze_hotel_patterns(self, adjustments: List[RouteAdjustment]) -> List[Dict]:
        """ホテル別の調整パターン"""
        hotel_stats = defaultdict(lambda: {
            'total_adjustments': 0,
            'reorder_count': 0,
            'reassign_count': 0,
            'time_change_count': 0
        })
        
        for adj in adjustments:
            affected_hotels = set()
            
            # 影響を受けたゲストのホテルを特定
            if adj.affected_guests:
                for guest_id in adj.affected_guests:
                    guest = self.db.query(Guest).filter(Guest.id == guest_id).first()
                    if guest and guest.hotel_name:
                        affected_hotels.add(guest.hotel_name)
            
            # ホテル別に統計を更新
            for hotel in affected_hotels:
                hotel_stats[hotel]['total_adjustments'] += 1
                
                if adj.adjustment_type == AdjustmentType.reorder:
                    hotel_stats[hotel]['reorder_count'] += 1
                elif adj.adjustment_type == AdjustmentType.reassign:
                    hotel_stats[hotel]['reassign_count'] += 1
                elif adj.adjustment_type == AdjustmentType.time_change:
                    hotel_stats[hotel]['time_change_count'] += 1
        
        # 結果を整形
        results = []
        for hotel, stats in hotel_stats.items():
            if stats['total_adjustments'] >= 5:  # 5回以上調整があったホテル
                results.append({
                    "hotel_name": hotel,
                    "statistics": stats,
                    "primary_issue": self._identify_primary_issue(stats),
                    "recommendation": self._generate_hotel_recommendation(hotel, stats)
                })
        
        return sorted(results, key=lambda x: x['statistics']['total_adjustments'], reverse=True)
    
    def _identify_primary_issue(self, stats: Dict) -> str:
        """主な問題を特定"""
        if stats['reorder_count'] > stats['reassign_count'] and stats['reorder_count'] > stats['time_change_count']:
            return "frequent_reordering"
        elif stats['reassign_count'] > stats['time_change_count']:
            return "frequent_reassignment"
        else:
            return "frequent_time_changes"
    
    def _generate_hotel_recommendation(self, hotel: str, stats: Dict) -> str:
        """ホテル別の推奨事項を生成"""
        primary_issue = self._identify_primary_issue(stats)
        
        if primary_issue == "frequent_reordering":
            return f"{hotel}のピックアップ順序を見直すことを推奨"
        elif primary_issue == "frequent_reassignment":
            return f"{hotel}の車両割り当て基準を見直すことを推奨"
        else:
            return f"{hotel}のピックアップ時間枠を調整することを推奨"
    
    def _analyze_distance_impact(self, adjustments: List[RouteAdjustment]) -> Dict:
        """調整による距離への影響を分析"""
        impacts = []
        
        for adj in adjustments:
            if adj.impact_distance_km is not None:
                impacts.append({
                    'type': adj.adjustment_type.value,
                    'distance_change': adj.impact_distance_km,
                    'time_change': adj.impact_time_minutes or 0
                })
        
        if not impacts:
            return {}
        
        df = pd.DataFrame(impacts)
        
        return {
            'average_distance_increase': float(df['distance_change'].mean()),
            'average_time_increase': float(df['time_change'].mean()),
            'by_type': df.groupby('type').agg({
                'distance_change': 'mean',
                'time_change': 'mean'
            }).to_dict()
        }
    
    def _analyze_adjustment_reasons(self, adjustments: List[RouteAdjustment]) -> List[Dict]:
        """調整理由の分析"""
        reasons = []
        
        for adj in adjustments:
            if adj.reason:
                reasons.append(adj.reason.lower())
        
        reason_counts = Counter(reasons)
        
        return [
            {
                "reason": reason,
                "count": count,
                "percentage": count / len(reasons) * 100 if reasons else 0
            }
            for reason, count in reason_counts.most_common(10)
        ]
    
    def _generate_recommendations(self, patterns: Dict) -> List[Dict]:
        """分析結果から推奨事項を生成"""
        recommendations = []
        
        # 1. ゲストペアの推奨事項
        if patterns.get('frequent_swaps'):
            recommendations.append({
                "type": "guest_pairing",
                "priority": "high",
                "title": "ゲストの組み合わせ最適化",
                "description": "特定のゲストペアを同じ車両に割り当てないことを推奨",
                "details": patterns['frequent_swaps'][:3],  # 上位3ペア
                "expected_impact": "調整作業を約20%削減"
            })
        
        # 2. 時間帯の推奨事項
        if patterns.get('time_patterns'):
            time_recommendations = []
            for hotel, pattern in patterns['time_patterns'].items():
                if pattern.get('preferred_pickup_hour') is not None:
                    time_recommendations.append({
                        "hotel": hotel,
                        "recommended_time": f"{pattern['preferred_pickup_hour']}:00",
                        "current_adjustments": pattern['total_adjustments']
                    })
            
            if time_recommendations:
                recommendations.append({
                    "type": "pickup_time",
                    "priority": "medium",
                    "title": "ピックアップ時間の最適化",
                    "description": "ホテル別の推奨ピックアップ時間を設定",
                    "details": time_recommendations[:5],
                    "expected_impact": "時間調整を約30%削減"
                })
        
        # 3. ホテル順序の推奨事項
        if patterns.get('hotel_patterns'):
            problematic_hotels = [
                hp for hp in patterns['hotel_patterns'] 
                if hp['primary_issue'] == 'frequent_reordering'
            ]
            
            if problematic_hotels:
                recommendations.append({
                    "type": "hotel_sequence",
                    "priority": "medium",
                    "title": "ホテル巡回順序の見直し",
                    "description": "頻繁に順序変更されるホテルの優先順位を調整",
                    "details": problematic_hotels[:3],
                    "expected_impact": "ルート再計算を約15%削減"
                })
        
        return recommendations
    
    def _generate_learning_rules(self, patterns: Dict) -> List[Dict]:
        """最適化エンジンに適用する学習ルールを生成"""
        rules = []
        
        # 1. ゲスト非互換性ルール
        for swap in patterns.get('frequent_swaps', []):
            if swap['frequency'] >= 3:
                rules.append({
                    "rule_type": "guest_incompatibility",
                    "parameters": {
                        "guest1_id": swap['guest_pair']['guest1']['id'],
                        "guest2_id": swap['guest_pair']['guest2']['id']
                    },
                    "strength": min(1.0, swap['frequency'] / 10),
                    "description": f"ゲストペアを別車両に配置"
                })
        
        # 2. 時間窓調整ルール
        for hotel, pattern in patterns.get('time_patterns', {}).items():
            if pattern.get('preferred_pickup_hour') is not None:
                rules.append({
                    "rule_type": "preferred_time_window",
                    "parameters": {
                        "hotel_name": hotel,
                        "preferred_hour": pattern['preferred_pickup_hour'],
                        "flexibility_minutes": 30
                    },
                    "strength": 0.8,
                    "description": f"{hotel}の推奨ピックアップ時間"
                })
        
        # 3. ホテル優先順位ルール
        hotel_priorities = []
        for hp in patterns.get('hotel_patterns', []):
            if hp['statistics']['total_adjustments'] >= 10:
                priority_score = 1.0 - (hp['statistics']['reorder_count'] / 
                                      hp['statistics']['total_adjustments'])
                hotel_priorities.append({
                    "hotel_name": hp['hotel_name'],
                    "priority": priority_score
                })
        
        if hotel_priorities:
            rules.append({
                "rule_type": "hotel_priority",
                "parameters": {
                    "priorities": sorted(
                        hotel_priorities, 
                        key=lambda x: x['priority'], 
                        reverse=True
                    )
                },
                "strength": 0.7,
                "description": "ホテル巡回優先順位"
            })
        
        return rules