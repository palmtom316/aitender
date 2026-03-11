from itertools import count
from pathlib import Path

from app.integrations.ocr.commercial_adapter import CommercialOCRAdapter
from app.integrations.ocr.mineru_adapter import MineruOCRAdapter
from app.models.norm_processing_job import (
    NormProcessingJob,
    NormProcessingJobStatus,
)


class OCRDispatcher:
    def __init__(self, adapters: dict[str, object] | None = None) -> None:
        self._id_sequence = count(1)
        self._adapters = adapters or {
            "mineru": MineruOCRAdapter(),
            "commercial": CommercialOCRAdapter(),
        }

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

        adapter = self._adapters[provider_name]
        try:
            result = adapter.extract(document_path)
        except Exception as exc:
            job.status = NormProcessingJobStatus.FAILED
            job.error_message = str(exc)
            return job, None

        job.status = NormProcessingJobStatus.COMPLETED
        return job, result


ocr_dispatcher = OCRDispatcher()
