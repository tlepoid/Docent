"""Configuration loading for Docent.

Reads from environment variables with optional .env file support.
Follows the existing application pattern — no new config mechanisms.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    ai_provider: str = "claude"              # "claude" | "azure_openai"
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-sonnet-4-6"
    azure_api_key: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_deployment: Optional[str] = None
    azure_api_version: str = "2024-02-01"


def load_config() -> Config:
    """Load configuration from environment variables (and optional .env file)."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv is optional

    return Config(
        ai_provider=os.getenv("AI_PROVIDER", "claude"),
        claude_api_key=os.getenv("ANTHROPIC_API_KEY"),
        claude_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
        azure_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
    )


def build_provider(config: Optional[Config] = None):
    """Instantiate the AI provider selected by configuration."""
    if config is None:
        config = load_config()

    if config.ai_provider == "claude":
        from .ai.providers.claude import ClaudeProvider
        return ClaudeProvider(api_key=config.claude_api_key, model=config.claude_model)

    if config.ai_provider == "azure_openai":
        from .ai.providers.azure_openai import AzureOpenAIProvider
        return AzureOpenAIProvider(
            api_key=config.azure_api_key,
            azure_endpoint=config.azure_endpoint,
            deployment_name=config.azure_deployment,
            api_version=config.azure_api_version,
        )

    raise ValueError(
        f"Unknown AI_PROVIDER '{config.ai_provider}'. Supported: claude, azure_openai"
    )
