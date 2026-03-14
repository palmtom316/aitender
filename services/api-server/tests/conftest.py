import pytest

from app.repositories.factory import get_norm_structure_repository


@pytest.fixture(autouse=True)
def _reset_norm_structure_repository():
    repo = get_norm_structure_repository()
    repo.reset()
    yield
    repo.reset()

