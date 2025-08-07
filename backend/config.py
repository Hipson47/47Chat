# backend/config.py
"""
Centralized configuration using pydantic-settings.
Loads settings from environment variables and optional .env file.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Project configuration settings.

    Values are loaded from environment variables and the `.env` file.
    """

    # LLM / Orchestration
    OLLAMA_MODEL: str = Field(default="llama3", description="Default Ollama model name")

    # Paths
    META_PROMPT_PATH: str = Field(
        default="backend/orchestrator/meta_prompt.yaml",
        description="Path to the orchestrator meta prompt configuration file",
    )
    FAISS_STORE_PATH: str = Field(
        default="rag_store.faiss", description="Path to the FAISS index file"
    )
    CHUNKS_PATH: str = Field(
        default="rag_chunks.json", description="Path to the persisted chunks JSON file"
    )

    # pydantic-settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Export a singleton settings instance
settings = Settings()
