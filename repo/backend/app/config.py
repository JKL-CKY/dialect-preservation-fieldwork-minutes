from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./data/dialect.db"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    PYANNOTE_AUTH_TOKEN: str = ""
    HF_API_TOKEN: str = ""

    WHISPER_MODEL: str = "large-v3"
    WHISPER_LANGUAGE: str = "zh"

    SPACY_MODEL: str = "zh_core_web_trf"

    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@dialect-preservation.org"

    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
