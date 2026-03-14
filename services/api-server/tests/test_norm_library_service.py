from pathlib import Path

from app.core.config import settings
from app.models.user import AuthenticatedUser, UserRole
from app.services.document_service import DocumentService
from app.services.norm_library_service import NormLibraryService
from app.services.ocr_dispatcher import OCRDispatcher
from app.workers.process_norm_document import process_norm_document


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


def test_norm_library_service_reads_documents_bundle_and_search(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(settings, "storage_root", tmp_path / "storage-root")
    user = AuthenticatedUser(
        id="user-pm",
        organization_id="org-1",
        role=UserRole.PROJECT_MANAGER,
        display_name="Project Manager",
    )
    documents = DocumentService(
        state_path=tmp_path / "documents.json",
        storage_root=tmp_path / "storage-root",
    )
    dispatcher = OCRDispatcher(
        adapters={"mineru": FakeSuccessAdapter()},
        state_path=tmp_path / "jobs.json",
    )
    library = NormLibraryService(documents=documents)
    document, _version, artifact = documents.create_upload(
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
        documents=documents,
    )

    documents_list = library.list_documents(project_id="project-alpha")
    bundle = library.get_bundle(project_id="project-alpha", document_id=document.id)
    search = library.search(
        project_id="project-alpha",
        document_id=document.id,
        query="implementation scope",
    )
    version = documents.get_current_version(document.id)
    assert version is not None
    artifact_types = {
        artifact.artifact_type
        for artifact in documents.list_artifacts_for_version(version.id)
    }

    assert raw_result is not None
    assert "clause_index_json" in artifact_types
    assert "commentary_json" in artifact_types
    assert "validation_json" in artifact_types
    assert "quality_report_json" in artifact_types
    assert documents_list == [
        {
            "id": document.id,
            "file_name": "grid-standard.pdf",
            "latest_job_id": job.id,
            "status": "indexed",
            "library_type": "norm_library",
        }
    ]
    assert bundle is not None
    assert bundle["document"]["latest_job_id"] == job.id
    assert bundle["tree"][0]["label"] == "1"
    assert bundle["commentary_results"] == []
    assert bundle["results"] == [
        {
            "label": "1.0.1",
            "title": "General clause text for the project.",
            "page_start": 1,
            "page_end": 1,
            "summary_text": "General clause text for the project.",
            "commentary_summary": "",
            "content_preview": "1.0.1 General clause text for the project.",
            "path_labels": ["1", "1.0.1"],
            "tags": [],
        },
        {
            "label": "1.1.1",
            "title": "Scope clause text that explains the implementation scope.",
            "page_start": 1,
            "page_end": 1,
            "summary_text": "Scope clause text that explains the implementation scope.",
            "commentary_summary": "",
            "content_preview": "1.1.1 Scope clause text that explains the implementation scope.",
            "path_labels": ["1", "1.1", "1.1.1"],
            "tags": [],
        },
    ]
    assert search == {
        "items": [
            {
                "label": "1.1.1",
                "title": "Scope clause text that explains the implementation scope.",
                "page_start": 1,
                "page_end": 1,
                "summary_text": "Scope clause text that explains the implementation scope.",
                "commentary_summary": "",
                "content_preview": "1.1.1 Scope clause text that explains the implementation scope.",
                "path_labels": ["1", "1.1", "1.1.1"],
                "tags": [],
            }
        ],
        "commentary_items": []
    }
