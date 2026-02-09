"""Configuration settings for the MCP server."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MCP server configuration loaded from environment variables."""

    supabase_url: str
    supabase_anon_key: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
