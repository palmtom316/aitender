from abc import ABC, abstractmethod

from app.models.norm_processing_job import NormProcessingJob


class ProcessingJobRepository(ABC):
    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def next_job_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_job(self, job_id: str) -> NormProcessingJob | None:
        raise NotImplementedError

    @abstractmethod
    def save_job(self, job: NormProcessingJob) -> None:
        raise NotImplementedError
