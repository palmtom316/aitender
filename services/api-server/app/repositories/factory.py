from functools import lru_cache

from app.core.config import settings
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.json_audit_log_repository import JsonAuditLogRepository
from app.repositories.json_document_repository import JsonDocumentRepository
from app.repositories.json_norm_structure_repository import JsonNormStructureRepository
from app.repositories.json_processing_job_repository import JsonProcessingJobRepository
from app.repositories.json_project_repository import JsonProjectRepository
from app.repositories.norm_structure_repository import NormStructureRepository
from app.repositories.postgres_audit_log_repository import PostgresAuditLogRepository
from app.repositories.postgres_document_repository import PostgresDocumentRepository
from app.repositories.postgres_norm_structure_repository import (
    PostgresNormStructureRepository,
)
from app.repositories.postgres_processing_job_repository import (
    PostgresProcessingJobRepository,
)
from app.repositories.postgres_project_repository import PostgresProjectRepository
from app.repositories.processing_job_repository import ProcessingJobRepository
from app.repositories.project_repository import ProjectRepository


def _backend() -> str:
    backend = settings.repository_backend.lower()
    if backend not in {"json", "postgres"}:
        raise RuntimeError(f"Unsupported repository backend: {settings.repository_backend}")
    return backend


@lru_cache(maxsize=1)
def get_project_repository() -> ProjectRepository:
    if _backend() == "postgres":
        return PostgresProjectRepository()
    return JsonProjectRepository()


@lru_cache(maxsize=1)
def get_document_repository() -> DocumentRepository:
    if _backend() == "postgres":
        return PostgresDocumentRepository()
    return JsonDocumentRepository()


@lru_cache(maxsize=1)
def get_audit_log_repository() -> AuditLogRepository:
    if _backend() == "postgres":
        return PostgresAuditLogRepository()
    return JsonAuditLogRepository()


@lru_cache(maxsize=1)
def get_processing_job_repository() -> ProcessingJobRepository:
    if _backend() == "postgres":
        return PostgresProcessingJobRepository()
    return JsonProcessingJobRepository()


@lru_cache(maxsize=1)
def get_norm_structure_repository() -> NormStructureRepository:
    if _backend() == "postgres":
        return PostgresNormStructureRepository()
    return JsonNormStructureRepository()


def reset_repository_factories() -> None:
    get_project_repository.cache_clear()
    get_document_repository.cache_clear()
    get_audit_log_repository.cache_clear()
    get_processing_job_repository.cache_clear()
    get_norm_structure_repository.cache_clear()
