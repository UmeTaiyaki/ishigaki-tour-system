# backend/app/api/v1/endpoints/analytics.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from uuid import UUID

from app.models.database import get_db
from app.services.learning_service import LearningService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/patterns", response_model=Dict[str, Any])
async def get_optimization_patterns(
    days: int = Query(90, description="分析期間（日数）", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    最適化パターンの分析結果を取得
    
    過去の調整データを分析して、パターンと推奨事項を返します。
    """
    learning_service = LearningService(db)
    
    try:
        patterns = await learning_service.analyze_adjustment_patterns(days)
        return patterns
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        return {
            "status": "error",
            "message": str(e),
            "patterns": {},
            "recommendations": [],
            "learning_rules": []
        }


@router.post("/apply-learning/{tour_id}")
async def apply_learning_to_tour(
    tour_id: str,
    learning_days: int = Query(90, description="学習に使用する過去データの日数", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    学習結果を特定のツアーに適用
    
    過去の調整パターンから学習したルールを、指定されたツアーの最適化に適用します。
    """
    from app.crud.tour import tour as crud_tour
    
    try:
        tour_uuid = UUID(tour_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tour ID format")
    
    tour = crud_tour.get(db, tour_id=tour_uuid)
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    learning_service = LearningService(db)
    
    # 分析を実行
    analysis = await learning_service.analyze_adjustment_patterns(learning_days)
    
    # 学習ルールの適用（実際の適用ロジックはOptimizationRequestで処理）
    applied_rules = []
    for rule in analysis.get('learning_rules', []):
        if rule['strength'] >= 0.5:  # 強度が50%以上のルールのみ適用
            applied_rules.append({
                "rule_type": rule['rule_type'],
                "description": rule['description'],
                "strength": rule['strength']
            })
    
    return {
        "status": "success",
        "tour_id": tour_id,
        "learning_rules_applied": len(applied_rules),
        "applied_rules": applied_rules,
        "recommendations": analysis.get('recommendations', [])[:3]  # 上位3つの推奨事項
    }


@router.get("/performance-metrics")
async def get_performance_metrics(
    days: int = Query(30, description="集計期間（日数）", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    システムのパフォーマンスメトリクスを取得
    
    最適化の成功率、平均計算時間、削減効果などの指標を返します。
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from app.models.tour import Tour
    from app.models.optimized_route import OptimizedRoute
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # ツアー統計
    total_tours = db.query(func.count(Tour.id)).filter(
        Tour.created_at >= cutoff_date
    ).scalar()
    
    optimized_tours = db.query(func.count(Tour.id)).filter(
        Tour.created_at >= cutoff_date,
        Tour.status.in_(['confirmed', 'completed'])
    ).scalar()
    
    # 最適化結果の統計
    optimization_stats = db.query(
        func.avg(OptimizedRoute.total_distance_km).label('avg_distance'),
        func.avg(OptimizedRoute.total_time_minutes).label('avg_time'),
        func.avg(OptimizedRoute.efficiency_score).label('avg_efficiency')
    ).join(Tour).filter(
        Tour.created_at >= cutoff_date
    ).first()
    
    return {
        "period": {
            "start": cutoff_date.date().isoformat(),
            "end": datetime.now().date().isoformat(),
            "days": days
        },
        "tour_metrics": {
            "total_tours": total_tours,
            "optimized_tours": optimized_tours,
            "optimization_rate": (optimized_tours / total_tours * 100) if total_tours > 0 else 0
        },
        "optimization_metrics": {
            "average_distance_km": float(optimization_stats.avg_distance or 0),
            "average_time_minutes": float(optimization_stats.avg_time or 0),
            "average_efficiency_score": float(optimization_stats.avg_efficiency or 0)
        }
    }