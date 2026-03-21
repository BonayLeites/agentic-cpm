from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/cpm"

    # Azure AI Foundry
    azure_ai_endpoint: str = ""
    azure_ai_api_key: str = ""
    azure_ai_deployment_gpt4o: str = "gpt-4o"
    azure_ai_deployment_mini: str = "gpt-4o-mini"

    # Application
    app_version: str = "1.0.0"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
