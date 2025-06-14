from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
import os
import traceback

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 設定のインポート
from app.core.config import settings
from app.api.v1.api import api_router

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時の処理
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info("Initializing OR-Tools...")
    
    # OR-Toolsのインポートチェック
    try:
        from ortools.constraint_solver import pywrapcp
        logger.info("✅ OR-Tools successfully loaded")
    except ImportError as e:
        logger.warning(f"⚠️ OR-Tools not available: {e}")
    
    yield
    
    # 終了時の処理
    logger.info("Shutting down application...")


# FastAPIアプリケーション作成
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# エラーハンドリングミドルウェア
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        # エラーの詳細をログに出力
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(f"Request path: {request.url.path}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # クライアントには簡潔なエラーメッセージを返す
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {str(e)}"}
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
    logger.info(f"CORS enabled for origins: {settings.BACKEND_CORS_ORIGINS}")

# APIルーター登録
app.include_router(api_router, prefix=settings.API_V1_STR)
logger.info(f"API router mounted at {settings.API_V1_STR}")

# ルートエンドポイント
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "openapi_url": f"{settings.API_V1_STR}/openapi.json"
    }

# ヘルスチェック
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION
    }

# デバッグ情報エンドポイント
@app.get("/debug/info")
async def debug_info():
    """デバッグ用の情報を返す"""
    import app as app_module
    return {
        "app_path": os.path.dirname(app_module.__file__),
        "python_path": sys.path[:5],  # 最初の5つのパス
        "current_dir": os.getcwd(),
        "api_prefix": settings.API_V1_STR,
        "docs_url": app.docs_url,
        "openapi_url": app.openapi_url,
        "routes": [{"path": route.path, "name": route.name} for route in app.routes if hasattr(route, 'path')]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")