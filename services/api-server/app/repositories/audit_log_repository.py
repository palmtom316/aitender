from abc import ABC, abstractmethod


class AuditLogRepository(ABC):
    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def append(
        self,
        *,
        job_id: str,
        step: str,
        message: str,
        level: str = "info",
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_for_job(self, job_id: str) -> list[dict]:
        raise NotImplementedError
