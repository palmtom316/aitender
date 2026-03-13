from pathlib import Path

from app.core.config import settings
from app.models.project_ai_settings import ProjectAiSettings
from app.repositories.json_state_store import JsonStateStore


class ProjectAiSettingsService:
    def __init__(self, state_path: Path | None = None) -> None:
        self._store = JsonStateStore(
            state_path or settings.state_root / "project_ai_settings.json",
        )
        self._store.load(default_factory=self._default_state)

    def reset(self) -> None:
        self._store.reset()
        self._store.load(default_factory=self._default_state)

    def get_settings(self, project_id: str) -> ProjectAiSettings:
        state = self._store.load(default_factory=self._default_state)
        payload = state["projects"].get(project_id)
        if payload is None:
            settings_model = ProjectAiSettings(project_id=project_id)
            state["projects"][project_id] = settings_model.model_dump(mode="json")
            self._store.save(state)
            return settings_model
        return ProjectAiSettings.model_validate(payload)

    def update_settings(
        self,
        project_id: str,
        payload: ProjectAiSettings,
    ) -> ProjectAiSettings:
        state = self._store.load(default_factory=self._default_state)
        settings_model = payload.model_copy(update={"project_id": project_id})
        state["projects"][project_id] = settings_model.model_dump(mode="json")
        self._store.save(state)
        return settings_model

    @staticmethod
    def _default_state() -> dict:
        return {"projects": {}}


project_ai_settings_service = ProjectAiSettingsService()
