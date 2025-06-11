from fastapi import APIRouter

from app.api.v1.endpoints import optimize

api_router = APIRouter()

# 最適化エンドポイント（最優先実装）
api_router.include_router(
    optimize.router,
    prefix="/optimize",
    tags=["optimization"]
)