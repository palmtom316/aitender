import os
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "aitender-api"
    environment: str = "development"
    state_root: Path = Path(os.environ.get("AITENDER_STATE_ROOT", "tmp/state"))
    storage_root: Path = Path(os.environ.get("AITENDER_STORAGE_ROOT", "tmp/storage"))
    repository_backend: str = os.environ.get("AITENDER_REPOSITORY_BACKEND", "json")
    database_url: str | None = os.environ.get("AITENDER_DATABASE_URL")


settings = Settings()
