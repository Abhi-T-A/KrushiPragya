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

    # Authentication & JWT Configuration
    JWT_SECRET: Optional[str] = Field(
        default=None,
        description="Supabase project JWT secret for validating authentication tokens",
    )
    JWT_SECRET_KEY: Optional[str] = Field(
        default=None,
        description="Secret key used for signing/verifying fallback JWT tokens",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="Algorithm used for signing JWT tokens")
    JWT_AUDIENCE: Optional[str] = Field(
        default=None,
        description="Expected JWT audience claim (e.g. 'authenticated')",
    )
    JWT_ISSUER: Optional[str] = Field(
        default=None,
        description="Expected JWT issuer claim",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, description="Token expiration window in minutes (default 24h)")

    @property
    def effective_jwt_secret(self) -> Optional[str]:
        """Return configured Supabase JWT secret or fallback to secret key."""
        return self.JWT_SECRET or self.JWT_SECRET_KEY


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

    # Market Data Provider Configuration (OGD India / AGMARKNET / e-NAM)
    DATA_GOV_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for Data.gov.in (Open Government Data Platform India)",
    )
    DATA_GOV_RESOURCE_ID: str = Field(
        default="9ef84268-d588-465a-a308-a864a43d0070",
        description="Data.gov.in dataset resource ID for Current Daily Mandi Prices",
    )
    DATA_GOV_BASE_URL: str = Field(
        default="https://api.data.gov.in/resource",
        description="Base URL for Data.gov.in resource API",
    )
    AGMARKNET_BASE_URL: str = Field(
        default="https://agmarknet.gov.in",
        description="Base URL for AGMARKNET portal",
    )
    ENAM_BASE_URL: str = Field(
        default="https://enam.gov.in",
        description="Base URL for e-NAM portal",
    )

    # Disease Detection Model Configuration
    DISEASE_MODEL_DIR: str = Field(
        default="",
        description="Path to directory containing trained disease classification model checkpoints (empty string defaults to <project_root>/models/disease)",
    )

    # LLM Provider Configuration (Groq, Ollama)
    LLM_PROVIDER: str = Field(
        default="ollama",
        description="Active LLM provider implementation ('ollama' or 'groq')",
    )
    LLM_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Base URL for LLM API server (e.g. http://localhost:11434 or https://api.groq.com/openai/v1)",
    )
    LLM_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for external LLM provider (e.g. Groq)",
    )
    LLM_MODEL: str = Field(
        default="qwen3:8b",
        description="Model identifier to use for LLM text generation (e.g. qwen3:8b or openai/gpt-oss-120b)",
    )
    LLM_TEMPERATURE: float = Field(
        default=0.0,
        description="Sampling temperature for LLM completions",
    )
    LLM_TIMEOUT: float = Field(
        default=300.0,
        description="Timeout in seconds for LLM inference requests",
    )

    # Legacy compatibility aliases for Ollama
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Legacy fallback for Ollama base URL",
    )
    OLLAMA_MODEL: str = Field(
        default="qwen3:8b",
        description="Legacy fallback for Ollama model name",
    )

    # Government Schemes Crawler & Intelligence Configuration
    SCHEME_CRAWLER_ENABLED: bool = Field(
        default=True,
        description="Master switch to enable/disable automated scheme crawling",
    )
    SCHEME_CRAWL_INTERVAL_HOURS: int = Field(
        default=5,
        description="Fixed crawl interval in hours (every 5 hours)",
    )
    SCHEME_CRAWL_TIMEOUT_SECONDS: int = Field(
        default=30,
        description="Request timeout in seconds for fetching scheme pages",
    )
    SCHEME_MAX_PAGES_PER_SOURCE: int = Field(
        default=100,
        description="Maximum pages to crawl per allowlisted source",
    )
    SCHEME_MAX_DOCUMENT_SIZE_MB: int = Field(
        default=10,
        description="Maximum allowed document size in megabytes",
    )
    SCHEME_REQUEST_DELAY_MS: int = Field(
        default=1000,
        description="Delay between requests to the same source in milliseconds",
    )
    SCHEME_MAX_RETRIES: int = Field(
        default=3,
        description="Maximum retry attempts with exponential backoff",
    )
    SCHEME_USER_AGENT: str = Field(
        default="KrushiPragya-SchemeBot/1.0 (+https://krushipragya.com/bot; bot@krushipragya.com)",
        description="User-Agent header sent to government scheme portals",
    )

    # Verification & Community Corroboration Configuration
    MIN_CORROBORATIONS_FOR_VERIFICATION: int = Field(
        default=2,
        description="Minimum number of agreeing community corroborations required to advance status from AI_ANALYSED to CORROBORATED",
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
