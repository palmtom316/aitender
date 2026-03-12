from pathlib import Path

from app.repositories.factory import get_audit_log_repository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.json_audit_log_repository import JsonAuditLogRepository


class AuditService:
    def __init__(
        self,
        state_path: Path | None = None,
        repository: AuditLogRepository | None = None,
    ) -> None:
        self._repository = (
            repository
            or JsonAuditLogRepository(state_path=state_path)
            if state_path is not None
            else get_audit_log_repository()
        )

    def reset(self) -> None:
        self._repository.reset()

    def record(
        self,
        *,
        job_id: str,
        step: str,
        message: str,
        level: str = "info",
    ) -> dict:
        return self._repository.append(
            job_id=job_id,
            step=step,
            message=message,
            level=level,
        )

    def list_for_job(self, job_id: str) -> list[dict]:
        return self._repository.list_for_job(job_id)


audit_service = AuditService(repository=get_audit_log_repository())
