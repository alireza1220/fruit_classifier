"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Zoom
    zoom_account_id: str = ""
    zoom_client_id: str = ""
    zoom_client_secret: str = ""
    zoom_webhook_secret_token: str = ""
    zoom_bot_display_name: str = "Instruction Bot (Recording)"

    # Whitelist
    zoom_whitelist_meeting_ids: str = ""
    zoom_whitelist_host_emails: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./zoombot.db"

    # Optional
    openai_api_key: str = ""
    redis_url: str = "redis://localhost:6379"

    @property
    def whitelist_meeting_ids(self) -> list[str]:
        if not self.zoom_whitelist_meeting_ids:
            return []
        return [x.strip() for x in self.zoom_whitelist_meeting_ids.split(",") if x.strip()]

    @property
    def whitelist_host_emails(self) -> list[str]:
        if not self.zoom_whitelist_host_emails:
            return []
        return [x.strip().lower() for x in self.zoom_whitelist_host_emails.split(",") if x.strip()]


settings = Settings()
