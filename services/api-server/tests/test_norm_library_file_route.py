from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_document_service
from app.main import app
from app.models.user import AuthenticatedUser, UserRole
from app.services.document_service import DocumentService


def test_norm_library_file_route_returns_uploaded_pdf(tmp_path: Path):
    documents = DocumentService(
        state_path=tmp_path / "documents.json",
        storage_root=tmp_path / "storage",
    )
    user = AuthenticatedUser(
        id="user-pm",
        organization_id="org-1",
        role=UserRole.PROJECT_MANAGER,
        display_name="Project Manager",
    )
    document, _version, _artifact = documents.create_upload(
        current_user=user,
        project_id="project-alpha",
        filename="grid-standard.pdf",
        content_type="application/pdf",
        content=b"%PDF-1.7 sample",
    )

    client = TestClient(app)
    app.dependency_overrides[get_document_service] = lambda: documents

    try:
        response = client.get(
            f"/projects/project-alpha/norm-library/documents/{document.id}/file",
            headers={"Authorization": "Bearer auth-token-pm"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == b"%PDF-1.7 sample"
    finally:
        app.dependency_overrides.clear()
