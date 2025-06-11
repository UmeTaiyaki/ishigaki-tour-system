from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict
import uuid
from datetime import datetime
import logging

from app.schemas.optimization import (
    OptimizationRequest,
    OptimizationResult,
    OptimizationJobStatus,
    Guest,
    Vehicle
)

logger = logging.getLogger(__name__)
router = APIRouter()

# 一時的なメモリストレージ（後でRedisやDBに置き換え）
optimization_jobs: Dict[str, OptimizationJobStatus] = {}


@router.post("/route", response_model=OptimizationJobStatus)
async def optimize_route(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks
):
    """
    ツアールートの最適化を開始する
    
    - 非同期処理として最適化を実行
    - ジョブIDを返却し、後でステータス確認可能
    """
    job_id = f"opt_job_{uuid.uuid4().hex[:8]}"
    
    # ジョブステータス初期化
    job_status = OptimizationJobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        estimated_completion_seconds=10,
        progress_percentage=0
    )
    
    optimization_jobs[job_id] = job_status
    
    # バックグラウンドで最適化実行
    background_tasks.add_task(
        run_optimization,
        job_id=job_id,
        request=request
    )
    
    logger.info(f"Optimization job started: {job_id}")
    return job_status


@router.get("/status/{job_id}", response_model=OptimizationJobStatus)
async def get_optimization_status(job_id: str):
    """最適化ジョブのステータスを取得"""
    if job_id not in optimization_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return optimization_jobs[job_id]


@router.get("/result/{job_id}", response_model=OptimizationResult)
async def get_optimization_result(job_id: str):
    """最適化結果を取得"""
    if job_id not in optimization_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_status = optimization_jobs[job_id]
    
    if job_status.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is {job_status.status}. Results not available yet."
        )
    
    if not job_status.result:
        raise HTTPException(status_code=500, detail="Result not found")
    
    return job_status.result


async def run_optimization(job_id: str, request: OptimizationRequest):
    """
    最適化を実行する（仮実装）
    Day 3-4でOR-Toolsを統合
    """
    try:
        # ステータス更新
        optimization_jobs[job_id].status = "processing"
        optimization_jobs[job_id].updated_at = datetime.now()
        optimization_jobs[job_id].progress_percentage = 10
        
        # TODO: ここで実際の最適化処理を実装
        # 1. ゲストと車両データを取得
        # 2. 距離行列を計算
        # 3. OR-Toolsで最適化
        # 4. 結果を整形
        
        # 仮の結果を生成（Day 1-2では仮実装）
        import asyncio
        await asyncio.sleep(2)  # 処理時間のシミュレーション
        
        result = OptimizationResult(
            tour_id=f"tour_{uuid.uuid4().hex[:8]}",
            status="success",
            total_vehicles_used=1,
            routes=[],
            total_distance_km=25.5,
            total_time_minutes=90,
            average_efficiency_score=0.85,
            optimization_metrics={
                "iterations": 100,
                "convergence": True
            },
            computation_time_seconds=2.0
        )
        
        # 結果を保存
        optimization_jobs[job_id].status = "completed"
        optimization_jobs[job_id].result = result
        optimization_jobs[job_id].progress_percentage = 100
        optimization_jobs[job_id].updated_at = datetime.now()
        
        logger.info(f"Optimization completed: {job_id}")
        
    except Exception as e:
        logger.error(f"Optimization failed for job {job_id}: {str(e)}")
        optimization_jobs[job_id].status = "failed"
        optimization_jobs[job_id].error_message = str(e)
        optimization_jobs[job_id].updated_at = datetime.now()