from app.models.norm_processing_job import NormProcessingJob
from app.repositories.id_factory import prefixed_uuid
from app.repositories.postgres_base import PostgresRepositoryBase
from app.repositories.processing_job_repository import ProcessingJobRepository


class PostgresProcessingJobRepository(PostgresRepositoryBase, ProcessingJobRepository):
    def reset(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("delete from processing_jobs")

    def next_job_id(self) -> str:
        return prefixed_uuid("norm-job")

    def get_job(self, job_id: str) -> NormProcessingJob | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select id, document_id, provider_name, status, error_message
                    from processing_jobs
                    where id = %s
                    """,
                    [job_id],
                )
                row = cursor.fetchone()
                return NormProcessingJob.model_validate(row) if row else None

    def save_job(self, job: NormProcessingJob) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into processing_jobs (
                        id, document_id, provider_name, status, error_message
                    ) values (%s, %s, %s, %s, %s)
                    on conflict (id) do update set
                        document_id = excluded.document_id,
                        provider_name = excluded.provider_name,
                        status = excluded.status,
                        error_message = excluded.error_message
                    """,
                    [
                        job.id,
                        job.document_id,
                        job.provider_name,
                        job.status,
                        job.error_message,
                    ],
                )
