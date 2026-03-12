from pathlib import Path

from app.integrations.ocr.commercial_adapter import CommercialOCRAdapter
from app.integrations.ocr.mineru_adapter import MineruOCRAdapter
from app.models.norm_processing_job import (
    NormProcessingJob,
    NormProcessingJobStatus,
)
from app.repositories.factory import get_processing_job_repository
from app.repositories.json_processing_job_repository import JsonProcessingJobRepository
from app.repositories.processing_job_repository import ProcessingJobRepository
from app.services.audit_service import AuditService, audit_service


class OCRDispatcher:
    def __init__(
        self,
        adapters: dict[str, object] | None = None,
        audit: AuditService = audit_service,
        state_path: Path | None = None,
        repository: ProcessingJobRepository | None = None,
    ) -> None:
        self._audit = audit
        self._repository = (
            repository
            or JsonProcessingJobRepository(state_path=state_path)
            if state_path is not None
            else get_processing_job_repository()
        )
        self._adapters = adapters or {
            "mineru": MineruOCRAdapter(),
            "commercial": CommercialOCRAdapter(),
        }

    def reset(
        self,
        adapters: dict[str, object] | None = None,
        *,
        clear_state: bool = True,
    ) -> None:
        if clear_state:
            self._repository.reset()
        self._adapters = adapters or {
            "mineru": MineruOCRAdapter(),
            "commercial": CommercialOCRAdapter(),
        }

    def get_job(self, job_id: str) -> NormProcessingJob | None:
        return self._repository.get_job(job_id)

    def process_document(
        self,
        *,
        document_id: str,
        document_path: Path,
        provider_name: str,
    ) -> tuple[NormProcessingJob, dict | None]:
        job = NormProcessingJob(
            id=self._repository.next_job_id(),
            document_id=document_id,
            provider_name=provider_name,
            status=NormProcessingJobStatus.RUNNING,
        )
        self._repository.save_job(job)
        self._audit.record(
            job_id=job.id,
            step="job_started",
            message=f"Started OCR processing with {provider_name}",
        )

        adapter = self._adapters.get(provider_name)
        if adapter is None:
            error_message = f"Unsupported OCR provider: {provider_name}"
            job.status = NormProcessingJobStatus.FAILED
            job.error_message = error_message
            self._repository.save_job(job)
            self._audit.record(
                job_id=job.id,
                step="ocr_failed",
                message=error_message,
                level="error",
            )
            return job, None

        try:
            result = adapter.extract(document_path)
        except Exception as exc:
            job.status = NormProcessingJobStatus.FAILED
            job.error_message = str(exc)
            self._repository.save_job(job)
            self._audit.record(
                job_id=job.id,
                step="ocr_failed",
                message=str(exc),
                level="error",
            )
            return job, None

        job.status = NormProcessingJobStatus.COMPLETED
        self._repository.save_job(job)
        self._audit.record(
            job_id=job.id,
            step="ocr_completed",
            message="OCR processing completed",
        )
        return job, result


ocr_dispatcher = OCRDispatcher(
    audit=audit_service,
    repository=get_processing_job_repository(),
)
