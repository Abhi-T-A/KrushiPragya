from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    APP_NAME: str = Field(default="KrushiPragya", description="Name of the application")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    ENVIRONMENT: str = Field(default="development", description="Runtime environment")
    DEBUG: bool = Field(default=True, description="Debug mode flag")
    DATABASE_URL: Optional[str] = Field(default="", description="PostgreSQL database connection URL")
    DIRECT_URL: Optional[str] = Field(default=None, description="Direct PostgreSQL connection URL for migrations")
    CORS_ORIGINS: List[str] = Field(default=["*"], description="Allowed CORS origins")

    # Weather Provider Configuration
    WEATHER_PROVIDER: str = Field(default="openweather", description="Active weather provider implementation")
    OPENWEATHER_API_KEY: Optional[str] = Field(default=None, description="API key for OpenWeatherMap")
    OPENWEATHER_BASE_URL: str = Field(
        default="https://api.openweathermap.org/data/2.5",
        description="Base URL for OpenWeatherMap API",
    )

    # Supabase Storage Configuration
    SUPABASE_URL: Optional[str] = Field(default=None, description="Supabase project URL")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(
        default=None, description="Supabase service role secret key (server-side only)"
    )
    SUPABASE_CROP_REPORT_BUCKET: str = Field(
        default="crop-report-images",
        description="Supabase storage bucket for crop reports",
    )

    # Disease Detection Model Configuration
    DISEASE_MODEL_DIR: str = Field(
        default="",
        description="Path to directory containing trained disease classification model checkpoints (empty string defaults to <project_root>/models/disease)",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def is_database_configured(self) -> bool:
        """Check if DATABASE_URL has been configured."""
        return bool(self.DATABASE_URL and self.DATABASE_URL.strip())

    @property
    def resolved_disease_model_dir(self) -> Path:
        """Resolve path to models/disease directory."""
        if self.DISEASE_MODEL_DIR and self.DISEASE_MODEL_DIR.strip():
            return Path(self.DISEASE_MODEL_DIR)
        return Path(__file__).resolve().parents[2] / "models" / "disease"


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton instance of Settings."""
    return Settings()


# Singleton settings instance
settings: Settings = get_settings()
