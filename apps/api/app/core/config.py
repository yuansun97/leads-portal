from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Leads Portal API"
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/leads"

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_resumes_bucket: str = "resumes"
    local_upload_dir: str = "uploads"

    @property
    def supabase_jwks_url(self) -> str:
        if not self.supabase_url:
            return ""
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"

    resend_api_key: str = ""
    resend_from: str = "Leads Portal <onboarding@resend.dev>"
    attorney_notify_email: str = "attorney@example.com"
    email_enabled: bool = True

    max_resume_bytes: int = 10 * 1024 * 1024
    allowed_resume_content_types: str = (
        "application/pdf,"
        "application/msword,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    outbox_poll_interval_seconds: float = 2.0
    outbox_batch_size: int = 10
    outbox_max_attempts: int = 8

    # Local-only: when true, Bearer "dev-token" authenticates as an attorney.
    # Never enable in production.
    dev_auth_bypass: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_content_types(self) -> set[str]:
        return {item.strip() for item in self.allowed_resume_content_types.split(",") if item.strip()}

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
