"""
Configuration Module.
Why this file exists: Centralizes all application settings using Pydantic BaseSettings.
Why this design was chosen: It provides type safety, validation, and easy loading from .env files or environment variables.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl


class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Enterprise Knowledge & Analytics Assistant"
    API_V1_STR: str = "/api/v1"
    
    # Security Settings
    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Database Settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "enterprise_db"
    POSTGRES_PORT: int = 5432

    # AI Settings
    OPENAI_API_KEY: str = ""
    CHROMA_PERSIST_DIR: str = "./chroma_db"


    @computed_field  # type: ignore[misc]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )


settings = Settings()
