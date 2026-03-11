from itertools import count
from pathlib import Path

from app.integrations.ocr.commercial_adapter import CommercialOCRAdapter
from app.integrations.ocr.mineru_adapter import MineruOCRAdapter
from app.models.norm_processing_job import (
    NormProcessingJob,
    NormProcessingJobStatus,
)
from app.services.audit_service import AuditService, audit_service


class OCRDispatcher:
    def __init__(
        self,
        adapters: dict[str, object] | None = None,
        audit: AuditService = audit_service,
    ) -> None:
        self._audit = audit
        self.reset(adapters=adapters)

    def reset(self, adapters: dict[str, object] | None = None) -> None:
        self._id_sequence = count(1)
        self._jobs: dict[str, NormProcessingJob] = {}
        self._adapters = adapters or {
            "mineru": MineruOCRAdapter(),
            "commercial": CommercialOCRAdapter(),
        }

    def get_job(self, job_id: str) -> NormProcessingJob | None:
        return self._jobs.get(job_id)

    def process_document(
        self,
        *,
        document_id: str,
        document_path: Path,
        provider_name: str,
    ) -> tuple[NormProcessingJob, dict | None]:
        job = NormProcessingJob(
            id=f"norm-job-{next(self._id_sequence)}",
            document_id=document_id,
            provider_name=provider_name,
            status=NormProcessingJobStatus.RUNNING,
        )
        self._jobs[job.id] = job
        self._audit.record(
            job_id=job.id,
            step="job_started",
            message=f"Started OCR processing with {provider_name}",
        )

        adapter = self._adapters[provider_name]
        try:
            result = adapter.extract(document_path)
        except Exception as exc:
            job.status = NormProcessingJobStatus.FAILED
            job.error_message = str(exc)
            self._audit.record(
                job_id=job.id,
                step="ocr_failed",
                message=str(exc),
                level="error",
            )
            return job, None

        job.status = NormProcessingJobStatus.COMPLETED
        self._audit.record(
            job_id=job.id,
            step="ocr_completed",
            message="OCR processing completed",
        )
        return job, result


ocr_dispatcher = OCRDispatcher()
