# backend/app/settings.py

from __future__ import annotations

from pydantic import BaseModel


class AppSettings(BaseModel):
    """Application settings for the FastAPI layer."""

    app_name: str = "geoChat v2"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    default_language: str = "fa"
    default_dataset_id: str = "urmia"


def get_settings() -> AppSettings:
    """Return application settings."""
    return AppSettings()
