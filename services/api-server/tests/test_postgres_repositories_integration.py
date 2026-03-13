import os
from pathlib import Path

import pytest


psycopg = pytest.importorskip("psycopg")

from app.models.user import AuthenticatedUser, UserRole
from app.repositories.bootstrap import initialize_postgres_database
from app.repositories.postgres_audit_log_repository import PostgresAuditLogRepository
from app.repositories.postgres_document_repository import PostgresDocumentRepository
from app.repositories.postgres_norm_structure_repository import (
    PostgresNormStructureRepository,
)
from app.repositories.postgres_processing_job_repository import (
    PostgresProcessingJobRepository,
)
from app.repositories.postgres_project_repository import PostgresProjectRepository
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from app.services.norm_library_service import NormLibraryService
from app.services.ocr_dispatcher import OCRDispatcher
from app.services.project_service import ProjectService
from app.workers.process_norm_document import process_norm_document


POSTGRES_TEST_URL = os.environ.get(
    "AITENDER_POSTGRES_TEST_URL",
    "postgresql://aitender:secret@localhost:55432/aitender",
)


def _postgres_available() -> bool:
    try:
        with psycopg.connect(POSTGRES_TEST_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute("select 1")
                cursor.fetchone()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _postgres_available(),
    reason="Local PostgreSQL test instance is not available on the configured test URL",
)


class FakeSuccessAdapter:
    def extract(self, document_path: Path):
        return {
            "provider": "mineru",
            "markdown_text": (
                "# 1 General\n"
                "1.0.1 General clause text for the project.\n\n"
                "## 1.1 Scope\n"
                "1.1.1 Scope clause text that explains the implementation scope.\n"
            ),
            "layout_payload": {
                "pages": [
                    {
                        "page": 1,
                        "text": (
                            "1 General 1.0.1 General clause text for the project. "
                            "1.1 Scope 1.1.1 Scope clause text that explains the "
                            "implementation scope."
                        ),
                    }
                ]
            },
            "metadata": {"source_path": str(document_path)},
        }


@pytest.fixture()
def postgres_repositories():
    initialize_postgres_database(database_url=POSTGRES_TEST_URL, seed=True)

    project_repository = PostgresProjectRepository(database_url=POSTGRES_TEST_URL)
    document_repository = PostgresDocumentRepository(database_url=POSTGRES_TEST_URL)
    audit_repository = PostgresAuditLogRepository(database_url=POSTGRES_TEST_URL)
    job_repository = PostgresProcessingJobRepository(database_url=POSTGRES_TEST_URL)
    norm_repository = PostgresNormStructureRepository(database_url=POSTGRES_TEST_URL)

    document_repository.reset()
    audit_repository.reset()
    job_repository.reset()
    norm_repository.reset()
    project_repository.reset()
    initialize_postgres_database(database_url=POSTGRES_TEST_URL, seed=True)

    return {
      "projects": project_repository,
      "documents": document_repository,
      "audit": audit_repository,
      "norms": norm_repository,
      "jobs": job_repository,
    }


def test_postgres_repositories_support_upload_processing_and_query(
    tmp_path: Path,
    postgres_repositories,
):
    project_service = ProjectService(repository=postgres_repositories["projects"])
    document_service = DocumentService(
        repository=postgres_repositories["documents"],
        storage_root=tmp_path / "storage",
    )
    audit_service = AuditService(repository=postgres_repositories["audit"])
    dispatcher = OCRDispatcher(
        adapters={"mineru": FakeSuccessAdapter()},
        audit=audit_service,
        repository=postgres_repositories["jobs"],
    )
    library = NormLibraryService(
        documents=document_service,
        structure_repository=postgres_repositories["norms"],
    )
    user = AuthenticatedUser(
        id="user-pm",
        organization_id="org-1",
        role=UserRole.PROJECT_MANAGER,
        display_name="Project Manager",
    )

    visible_projects = project_service.list_projects_for_user(user)
    document, _version, artifact = document_service.create_upload(
        current_user=user,
        project_id="project-alpha",
        filename="grid-standard.pdf",
        content_type="application/pdf",
        content=b"%PDF-1.7 sample",
    )
    job, raw_result = process_norm_document(
        document_id=document.id,
        document_path=Path(artifact.storage_path),
        provider_name="mineru",
        dispatcher=dispatcher,
        documents=document_service,
        structure_repository=postgres_repositories["norms"],
    )

    version = document_service.get_current_version(document.id)
    assert version is not None
    artifact_types = {
        stored_artifact.artifact_type
        for stored_artifact in document_service.list_artifacts_for_version(version.id)
    }

    bundle = library.get_bundle(project_id="project-alpha", document_id=document.id)
    search = library.search(
        project_id="project-alpha",
        document_id=document.id,
        query="implementation scope",
        path_prefix="1.1",
    )

    assert [project.id for project in visible_projects.items] == [
        "project-alpha",
        "project-beta",
    ]
    assert raw_result is not None
    assert job.status.value == "completed"
    assert "clause_index_json" not in artifact_types
    assert "commentary_json" not in artifact_types
    assert "validation_json" in artifact_types
    assert bundle is not None
    assert bundle["document"]["latest_job_id"] == job.id
    assert bundle["results"][0]["label"] == "1.0.1"
    assert bundle["tree"][0]["label"] == "1"
    assert search == {
        "items": [
            {
                "label": "1.1.1",
                "title": "Scope clause text that explains the implementation scope.",
                "page_start": 1,
                "page_end": 1,
                "summary_text": "Scope clause text that explains the implementation scope.",
                "commentary_summary": "",
                "path_labels": ["1", "1.1", "1.1.1"],
                "tags": [],
            }
        ]
    }
