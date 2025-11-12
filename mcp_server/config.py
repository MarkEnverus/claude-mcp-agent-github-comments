"""
Configuration management for GitHub PR Comment Agent
"""


from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and config files"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # GitHub settings
    github_token: str = Field(..., description="GitHub personal access token")
    github_repo: str | None = Field(
        default=None,
        description="Repository in format owner/repo (auto-detected from git remote if not provided)"
    )
    github_api_base_url: str = "https://api.github.com"

    # Anthropic settings
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    claude_model: str = "claude-sonnet-4-5-20250929"
    claude_max_tokens: int = 4096
    claude_temperature: float = 0.0

    # MCP Server settings
    mcp_server_port: int = 3000
    mcp_server_host: str = "localhost"

    # Logging
    log_level: str = "INFO"
    log_file: str = "pr-comment-agent.log"

    # Feature flags
    enable_auto_commit: bool = False
    enable_auto_push: bool = False
    enable_dry_run_mode: bool = True

    @property
    def repo_owner(self) -> str | None:
        """Extract owner from repo string"""
        if self.github_repo:
            return self.github_repo.split("/")[0]
        return None

    @property
    def repo_name(self) -> str | None:
        """Extract repo name from repo string"""
        if self.github_repo:
            return self.github_repo.split("/")[1]
        return None


def load_settings() -> Settings:
    """Load settings from environment and config files"""
    return Settings()
