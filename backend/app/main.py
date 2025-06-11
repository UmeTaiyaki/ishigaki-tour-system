from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.v1.api import api_router

# ロギング設定
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時の処理
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info("Initializing OR-Tools...")
    # ここでOR-Toolsの初期化や接続テストを実行
    
    yield
    
    # 終了時の処理
    logger.info("Shutting down application...")


# FastAPIアプリケーション作成
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS設定
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# APIルーター登録
app.include_router(api_router, prefix=settings.API_V1_STR)

# ルートエンドポイント
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }

# ヘルスチェック
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION
    }