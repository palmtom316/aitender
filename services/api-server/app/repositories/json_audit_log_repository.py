from pathlib import Path

from app.core.config import settings
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.json_state_store import JsonStateStore


class JsonAuditLogRepository(AuditLogRepository):
    def __init__(self, state_path: Path | None = None) -> None:
        self._store = JsonStateStore(
            state_path or settings.state_root / "audit_logs.json",
        )
        self._store.load(default_factory=self._default_state)

    def reset(self) -> None:
        self._store.reset()
        self._store.load(default_factory=self._default_state)

    def append(
        self,
        *,
        job_id: str,
        step: str,
        message: str,
        level: str = "info",
    ) -> dict:
        state = self._store.load(default_factory=self._default_state)
        event = {
            "id": f"audit-{state['next_id']}",
            "job_id": job_id,
            "step": step,
            "message": message,
            "level": level,
        }
        state["next_id"] += 1
        state["events"].append(event)
        self._store.save(state)
        return event

    def list_for_job(self, job_id: str) -> list[dict]:
        state = self._store.load(default_factory=self._default_state)
        return [
            {
                "job_id": event["job_id"],
                "step": event["step"],
                "message": event["message"],
                "level": event["level"],
            }
            for event in state["events"]
            if event["job_id"] == job_id
        ]

    @staticmethod
    def _default_state() -> dict:
        return {
            "next_id": 1,
            "events": [],
        }
