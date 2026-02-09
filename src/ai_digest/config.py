"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/ai_digest"

    # Anthropic
    anthropic_api_key: str = ""

    # GitHub
    github_token: str = ""

    # Email – Resend
    resend_api_key: str = ""
    digest_email_from: str = "digest@example.com"
    digest_email_to: str = ""  # comma-separated list

    # SMTP fallback
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # Digest schedule
    digest_time: str = "08:00"
    digest_timezone: str = "America/Argentina/Cordoba"

    # S3
    s3_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "ai-digest-snapshots"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"

    # Web output
    web_output_dir: str = "./output/web"

    # Logging
    log_level: str = "INFO"

    @property
    def email_recipients(self) -> list[str]:
        return [e.strip() for e in self.digest_email_to.split(",") if e.strip()]

    @property
    def sync_database_url(self) -> str:
        """Return a synchronous database URL for Alembic."""
        return self.database_url.replace("+asyncpg", "")


settings = Settings()
