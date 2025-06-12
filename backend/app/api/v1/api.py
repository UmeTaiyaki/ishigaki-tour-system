from fastapi import APIRouter

from app.api.v1.endpoints import optimize, guests, vehicles, tours

api_router = APIRouter()

# 最適化エンドポイント（最優先実装）
api_router.include_router(
    optimize.router,
    prefix="/optimize",
    tags=["optimization"]
)

# ゲスト管理エンドポイント
api_router.include_router(
    guests.router,
    prefix="/guests",
    tags=["guests"]
)

# 車両管理エンドポイント
api_router.include_router(
    vehicles.router,
    prefix="/vehicles",
    tags=["vehicles"]
)

# ツアー管理エンドポイント
api_router.include_router(
    tours.router,
    prefix="/tours",
    tags=["tours"]
)