from itertools import count


class AuditService:
    def __init__(self) -> None:
        self._id_sequence = count(1)
        self.reset()

    def reset(self) -> None:
        self._events: list[dict] = []

    def record(
        self,
        *,
        job_id: str,
        step: str,
        message: str,
        level: str = "info",
    ) -> dict:
        event = {
            "id": f"audit-{next(self._id_sequence)}",
            "job_id": job_id,
            "step": step,
            "message": message,
            "level": level,
        }
        self._events.append(event)
        return event

    def list_for_job(self, job_id: str) -> list[dict]:
        return [
            {
                "job_id": event["job_id"],
                "step": event["step"],
                "message": event["message"],
                "level": event["level"],
            }
            for event in self._events
            if event["job_id"] == job_id
        ]


audit_service = AuditService()
