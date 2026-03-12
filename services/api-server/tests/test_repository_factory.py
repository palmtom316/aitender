import pytest

from app.core.config import settings
from app.repositories.factory import (
    get_audit_log_repository,
    get_document_repository,
    get_norm_structure_repository,
    get_processing_job_repository,
    get_project_repository,
    reset_repository_factories,
)
from app.repositories.json_audit_log_repository import JsonAuditLogRepository
from app.repositories.json_document_repository import JsonDocumentRepository
from app.repositories.json_norm_structure_repository import JsonNormStructureRepository
from app.repositories.json_processing_job_repository import JsonProcessingJobRepository
from app.repositories.json_project_repository import JsonProjectRepository
from app.repositories.postgres_document_repository import PostgresDocumentRepository
from app.repositories.postgres_norm_structure_repository import (
    PostgresNormStructureRepository,
)


@pytest.fixture(autouse=True)
def restore_repository_settings():
    original_backend = settings.repository_backend
    original_database_url = settings.database_url
    reset_repository_factories()
    yield
    settings.repository_backend = original_backend
    settings.database_url = original_database_url
    reset_repository_factories()


def test_repository_factory_uses_json_backend_by_default():
    settings.repository_backend = "json"

    assert isinstance(get_project_repository(), JsonProjectRepository)
    assert isinstance(get_document_repository(), JsonDocumentRepository)
    assert isinstance(get_audit_log_repository(), JsonAuditLogRepository)
    assert isinstance(get_norm_structure_repository(), JsonNormStructureRepository)
    assert isinstance(get_processing_job_repository(), JsonProcessingJobRepository)


def test_repository_factory_requires_database_url_for_postgres_backend():
    settings.repository_backend = "postgres"
    settings.database_url = None

    with pytest.raises(RuntimeError, match="AITENDER_DATABASE_URL"):
        get_document_repository()


def test_repository_factory_can_construct_postgres_repository_without_connecting():
    settings.repository_backend = "postgres"
    settings.database_url = "postgresql://aitender:secret@localhost:5432/aitender"

    repository = get_document_repository()
    norm_repository = get_norm_structure_repository()

    assert isinstance(repository, PostgresDocumentRepository)
    assert isinstance(norm_repository, PostgresNormStructureRepository)
