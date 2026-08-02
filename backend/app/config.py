"""
Central configuration. Everything secret or environment-specific comes
from env vars (.env locally, real environment variables in production) --
never hardcode credentials in code.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "RAG Production App"
    ENVIRONMENT: str = "development"  # development | production
    SECRET_KEY: str  # used to sign JWTs -- generate with: openssl rand -hex 32

    # --- Database (Aiven Postgres) ---
    # Aiven requires SSL. Example:
    # postgresql+asyncpg://user:password@host:port/dbname?ssl=require
    DATABASE_URL: str

    # --- Auth ---
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # --- Google OAuth ---
    GOOGLE_CLIENT_ID: str = ""

    # --- LLM / Embeddings ---
    GENERATION_PROVIDER: str = "anthropic"  # anthropic | gemini
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "claude-sonnet-4-6"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    EMBEDDING_PROVIDER: str = "voyage"  # voyage | openai | gemini
    VOYAGE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    EMBEDDING_DIM: int = 1024  # must match the embedding model you use
    # voyage-3 -> 1024, text-embedding-3-small -> 1536, gemini text-embedding-004 -> 768

    # --- Uploads / guardrails ---
    MAX_UPLOAD_MB: int = 20
    MAX_PAGES_PER_PDF: int = 300
    RATE_LIMIT_PER_MINUTE: str = "20/minute"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
