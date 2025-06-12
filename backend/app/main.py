from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# インポートのデバッグ
print(f"Python path: {sys.path}")
print(f"Current directory: {os.getcwd()}")

try:
    from app.core.config import settings
    print("✅ Successfully imported settings")
except ImportError as e:
    print(f"❌ Failed to import settings: {e}")
    # フォールバック設定
    class Settings:
        API_V1_STR = "/api/v1"
        PROJECT_NAME = "石垣島ツアー最適化システム"
        VERSION = "0.1.0"
        BACKEND_CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]
        LOG_LEVEL = "INFO"
    settings = Settings()

try:
    from app.api.v1.api import api_router
    print("✅ Successfully imported api_router")
except ImportError as e:
    print(f"❌ Failed to import api_router: {e}")
    # フォールバックルーター
    from fastapi import APIRouter
    api_router = APIRouter()
    
    # optimize エンドポイントを直接インポート
    try:
        from app.api.v1.endpoints import optimize
        api_router.include_router(
            optimize.router,
            prefix="/optimize",
            tags=["optimization"]
        )
        print("✅ Successfully imported optimize endpoints")
    except ImportError as e:
        print(f"❌ Failed to import optimize endpoints: {e}")

# ロギング設定
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    openapi_url="/openapi.json",  # シンプルなパスに変更
    docs_url="/docs",  # 明示的に指定
    redoc_url="/redoc",  # ReDocも追加
    lifespan=lifespan
)

# CORS設定
if hasattr(settings, 'BACKEND_CORS_ORIGINS') and settings.BACKEND_CORS_ORIGINS:
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
        "docs": f"{settings.API_V1_STR}/docs"
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
    import app
    return {
        "app_path": os.path.dirname(app.__file__),
        "python_path": sys.path,
        "current_dir": os.getcwd(),
        "modules": list(sys.modules.keys())[:20]  # 最初の20モジュール
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)