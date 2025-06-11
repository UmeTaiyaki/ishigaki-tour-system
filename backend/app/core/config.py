from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API設定
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "石垣島ツアー最適化システム"
    VERSION: str = "0.1.0"
    
    # データベース（オプショナルに変更）
    DATABASE_URL: Optional[str] = "postgresql://user:password@localhost:5432/ishigaki_tour"
    SUPABASE_URL: Optional[str] = "https://your-project.supabase.co"
    SUPABASE_KEY: Optional[str] = "your-anon-key"
    
    # CORS設定
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Google Cloud（オプショナル）
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # 気象API
    WEATHER_API_BASE_URL: str = "https://api.open-meteo.com/v1"
    
    # OR-Tools設定
    OPTIMIZATION_TIME_LIMIT_SECONDS: int = 10
    MAX_VEHICLES: int = 10
    MAX_GUESTS_PER_OPTIMIZATION: int = 100
    
    # ログレベル
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
        # extra="forbid"を削除して、追加の環境変数を許可


settings = Settings()