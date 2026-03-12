from pathlib import Path

from app.models.user import AuthenticatedUser, UserRole
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from app.services.ocr_dispatcher import OCRDispatcher
from app.services.project_service import ProjectService


class FakeSuccessAdapter:
    def extract(self, document_path: Path):
        return {
            "provider": "mineru",
            "markdown_text": "# Sample",
            "layout_payload": {"pages": [{"page": 1, "text": "Sample"}]},
            "metadata": {"source_path": str(document_path)},
        }


def test_project_service_reloads_seed_state_from_disk(tmp_path: Path):
    state_path = tmp_path / "projects.json"
    writer = AuthenticatedUser(
        id="user-writer",
        organization_id="org-1",
        role=UserRole.WRITER,
        display_name="Writer",
    )

    initial = ProjectService(state_path=state_path)
    reloaded = ProjectService(state_path=state_path)

    assert initial.list_projects_for_user(writer).model_dump(mode="json") == (
        reloaded.list_projects_for_user(writer).model_dump(mode="json")
    )


def test_document_service_persists_uploaded_records_across_reloads(tmp_path: Path):
    service = DocumentService(
        state_path=tmp_path / "documents.json",
        storage_root=tmp_path / "storage",
    )
    user = AuthenticatedUser(
        id="user-pm",
        organization_id="org-1",
        role=UserRole.PROJECT_MANAGER,
        display_name="Project Manager",
    )

    document, version, artifact = service.create_upload(
        current_user=user,
        project_id="project-alpha",
        filename="grid-standard.pdf",
        content_type="application/pdf",
        content=b"%PDF-1.7 sample",
    )

    reloaded = DocumentService(
        state_path=tmp_path / "documents.json",
        storage_root=tmp_path / "storage",
    )

    assert document.id.startswith("doc-")
    assert version.id.startswith("doc-version-")
    assert artifact.id.startswith("artifact-")
    assert reloaded.document_count() == 1
    assert reloaded.get_document(document.id) == document
    assert Path(artifact.storage_path).read_bytes() == b"%PDF-1.7 sample"
    assert version.version_number == 1


def test_processing_jobs_and_audit_logs_survive_service_reload(tmp_path: Path):
    audit = AuditService(state_path=tmp_path / "audit.json")
    dispatcher = OCRDispatcher(
        adapters={"mineru": FakeSuccessAdapter()},
        audit=audit,
        state_path=tmp_path / "jobs.json",
    )
    source_file = tmp_path / "norm.pdf"
    source_file.write_bytes(b"%PDF-1.7 sample")

    job, result = dispatcher.process_document(
        document_id="doc-1",
        document_path=source_file,
        provider_name="mineru",
    )

    reloaded_audit = AuditService(state_path=tmp_path / "audit.json")
    reloaded_dispatcher = OCRDispatcher(
        adapters={"mineru": FakeSuccessAdapter()},
        audit=reloaded_audit,
        state_path=tmp_path / "jobs.json",
    )

    assert result is not None
    assert job.id.startswith("norm-job-")
    assert reloaded_dispatcher.get_job(job.id) == job
    assert reloaded_audit.list_for_job(job.id) == [
        {
            "job_id": job.id,
            "step": "job_started",
            "message": "Started OCR processing with mineru",
            "level": "info",
        },
        {
            "job_id": job.id,
            "step": "ocr_completed",
            "message": "OCR processing completed",
            "level": "info",
        },
    ]
