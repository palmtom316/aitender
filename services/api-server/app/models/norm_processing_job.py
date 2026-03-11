from enum import StrEnum

from pydantic import BaseModel


class NormProcessingJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class NormProcessingJob(BaseModel):
    id: str
    document_id: str
    provider_name: str
    status: NormProcessingJobStatus
    error_message: str | None = None
