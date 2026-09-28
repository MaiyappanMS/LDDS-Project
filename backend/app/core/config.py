from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables / .env (never hardcoded)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Learning Debt Detection System"
    environment: str = "development"
    frontend_url: str = "http://localhost:5173,http://127.0.0.1:5173"  # comma-separated list allowed


    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    ai_provider: str = "anthropic"  # anthropic | openai
    ai_api_key: str = ""
    ai_model: str = ""
    ai_base_url: str = ""
    ai_timeout_seconds: int = 90
    ai_max_input_chars: int = 30000

    max_upload_size_mb: int = 10
    min_syllabus_chars: int = 50

    # Mastery / learning-debt thresholds (percent). Change via env without touching code.
    threshold_high_debt: float = 40.0        # below -> HIGH_DEBT
    threshold_moderate_debt: float = 60.0    # below -> MODERATE_DEBT (still "weak")
    threshold_developing: float = 80.0       # below -> DEVELOPING, else MASTERED
    min_questions_for_full_confidence: int = 3
    mastery_window: int = 10                 # only the latest N answers per concept count
    default_questions_per_concept: int = 3
    escalation_dependents: int = 3           # weak concept blocking >= N concepts is escalated to "high"
    max_explanations_per_request: int = 3

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, v: str) -> str:
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            v = "postgresql+psycopg://" + v[len("postgresql://"):]
        return v

    @property
    def cors_origins(self) -> list[str]:
        return [
            o.strip().rstrip("/")
            for o in self.frontend_url.split(",")
            if o.strip()
        ]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
