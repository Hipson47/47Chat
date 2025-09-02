# backend/config.py
"""
Centralized configuration using pydantic-settings.
Loads settings from environment variables and optional .env file.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Project configuration settings.

    Values are loaded from environment variables and the `.env` file.
    """

    # LLM / Orchestration
    OLLAMA_MODEL: str = Field(default="llama3", description="Default Ollama model name")
    OPENAI_MODEL: str = Field(
        default="gpt-5-nano",
        description="Default OpenAI model name used by moderator/agents when OpenAI is selected",
    )
    ALTERS_LLM_PROVIDER: str = Field(
        default="ollama",
        description="Provider for alter agents: 'ollama' or 'openai'",
    )

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
