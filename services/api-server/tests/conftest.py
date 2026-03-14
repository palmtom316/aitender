import pytest

from app.repositories.factory import get_norm_structure_repository
from app.services.project_ai_settings_service import project_ai_settings_service


@pytest.fixture(autouse=True)
def _reset_norm_structure_repository():
    repo = get_norm_structure_repository()
    repo.reset()
    yield
    repo.reset()


@pytest.fixture(autouse=True)
def _reset_project_ai_settings_service():
    project_ai_settings_service.reset()
    yield
    project_ai_settings_service.reset()
