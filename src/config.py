from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    openai_api_key: str = Field(..., description="OpenAI-compatible API key")
    openai_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenAI-compatible API base URL",
    )
    openai_model: str = Field(
        default="openai/gpt-4o",
        description="LLM model identifier",
    )


settings = Settings()
