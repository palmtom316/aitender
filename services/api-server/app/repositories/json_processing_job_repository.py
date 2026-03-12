from pathlib import Path

from app.core.config import settings
from app.models.norm_processing_job import NormProcessingJob
from app.repositories.id_factory import prefixed_uuid
from app.repositories.json_state_store import JsonStateStore
from app.repositories.processing_job_repository import ProcessingJobRepository


class JsonProcessingJobRepository(ProcessingJobRepository):
    def __init__(self, state_path: Path | None = None) -> None:
        self._store = JsonStateStore(
            state_path or settings.state_root / "processing_jobs.json",
        )
        self._store.load(default_factory=self._default_state)

    def reset(self) -> None:
        self._store.reset()
        self._store.load(default_factory=self._default_state)

    def next_job_id(self) -> str:
        return prefixed_uuid("norm-job")

    def get_job(self, job_id: str) -> NormProcessingJob | None:
        state = self._store.load(default_factory=self._default_state)
        for job in state["jobs"]:
            if job["id"] == job_id:
                return NormProcessingJob.model_validate(job)
        return None

    def save_job(self, job: NormProcessingJob) -> None:
        state = self._store.load(default_factory=self._default_state)
        for index, current in enumerate(state["jobs"]):
            if current["id"] == job.id:
                state["jobs"][index] = job.model_dump(mode="json")
                self._store.save(state)
                return

        state["jobs"].append(job.model_dump(mode="json"))
        self._store.save(state)

    @staticmethod
    def _default_state() -> dict:
        return {
            "next_id": 1,
            "jobs": [],
        }
