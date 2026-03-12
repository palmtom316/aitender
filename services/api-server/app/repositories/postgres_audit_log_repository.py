from app.repositories.id_factory import prefixed_uuid
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.postgres_base import PostgresRepositoryBase


class PostgresAuditLogRepository(PostgresRepositoryBase, AuditLogRepository):
    def reset(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("delete from audit_logs")

    def append(
        self,
        *,
        job_id: str,
        step: str,
        message: str,
        level: str = "info",
    ) -> dict:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                event = {
                    "id": prefixed_uuid("audit"),
                    "job_id": job_id,
                    "step": step,
                    "message": message,
                    "level": level,
                }
                cursor.execute(
                    """
                    insert into audit_logs (id, job_id, step, message, level)
                    values (%s, %s, %s, %s, %s)
                    """,
                    [
                        event["id"],
                        job_id,
                        step,
                        message,
                        level,
                    ],
                )
                return event

    def list_for_job(self, job_id: str) -> list[dict]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select job_id, step, message, level
                    from audit_logs
                    where job_id = %s
                    order by created_at, id
                    """,
                    [job_id],
                )
                return list(cursor.fetchall())
