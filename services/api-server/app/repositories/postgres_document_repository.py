from app.models.document import Document
from app.models.document_artifact import DocumentArtifact
from app.models.document_version import DocumentVersion
from app.repositories.document_repository import DocumentRepository
from app.repositories.id_factory import prefixed_uuid
from app.repositories.postgres_base import PostgresRepositoryBase


class PostgresDocumentRepository(PostgresRepositoryBase, DocumentRepository):
    def reset(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("delete from document_artifacts")
                cursor.execute("delete from document_versions")
                cursor.execute("delete from documents")

    def next_identifier(self, prefix: str) -> str:
        return prefixed_uuid(prefix)

    def list_documents(self) -> list[Document]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select id, organization_id, project_id, file_name, library_type,
                           uploaded_by, status, current_version_id, latest_job_id
                    from documents
                    order by id
                    """
                )
                return [
                    Document.model_validate(row)
                    for row in cursor.fetchall()
                ]

    def get_document(self, document_id: str) -> Document | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select id, organization_id, project_id, file_name, library_type,
                           uploaded_by, status, current_version_id, latest_job_id
                    from documents
                    where id = %s
                    """,
                    [document_id],
                )
                row = cursor.fetchone()
                return Document.model_validate(row) if row else None

    def save_document(self, document: Document) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into documents (
                        id, organization_id, project_id, file_name, library_type,
                        uploaded_by, status, current_version_id, latest_job_id
                    ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    on conflict (id) do update set
                        organization_id = excluded.organization_id,
                        project_id = excluded.project_id,
                        file_name = excluded.file_name,
                        library_type = excluded.library_type,
                        uploaded_by = excluded.uploaded_by,
                        status = excluded.status,
                        current_version_id = excluded.current_version_id,
                        latest_job_id = excluded.latest_job_id
                    """,
                    [
                        document.id,
                        document.organization_id,
                        document.project_id,
                        document.file_name,
                        document.library_type,
                        document.uploaded_by,
                        document.status,
                        document.current_version_id,
                        document.latest_job_id,
                    ],
                )

    def get_current_version(self, document_id: str) -> DocumentVersion | None:
        document = self.get_document(document_id)
        if document is None or document.current_version_id is None:
            return None

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select id, document_id, version_number, source_file_name
                    from document_versions
                    where id = %s
                    """,
                    [document.current_version_id],
                )
                row = cursor.fetchone()
                return DocumentVersion.model_validate(row) if row else None

    def save_version(self, version: DocumentVersion) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into document_versions (
                        id, document_id, version_number, source_file_name
                    ) values (%s, %s, %s, %s)
                    on conflict (id) do update set
                        document_id = excluded.document_id,
                        version_number = excluded.version_number,
                        source_file_name = excluded.source_file_name
                    """,
                    [
                        version.id,
                        version.document_id,
                        version.version_number,
                        version.source_file_name,
                    ],
                )

    def list_artifacts_for_version(
        self,
        document_version_id: str,
    ) -> list[DocumentArtifact]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select id, document_version_id, artifact_type, storage_path
                    from document_artifacts
                    where document_version_id = %s
                    order by id
                    """,
                    [document_version_id],
                )
                return [
                    DocumentArtifact.model_validate(row)
                    for row in cursor.fetchall()
                ]

    def save_artifact(self, artifact: DocumentArtifact) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into document_artifacts (
                        id, document_version_id, artifact_type, storage_path
                    ) values (%s, %s, %s, %s)
                    on conflict (id) do update set
                        document_version_id = excluded.document_version_id,
                        artifact_type = excluded.artifact_type,
                        storage_path = excluded.storage_path
                    """,
                    [
                        artifact.id,
                        artifact.document_version_id,
                        artifact.artifact_type,
                        artifact.storage_path,
                    ],
                )
