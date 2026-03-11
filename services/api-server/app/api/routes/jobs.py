from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_audit_service, get_ocr_dispatcher
from app.services.audit_service import AuditService
from app.services.ocr_dispatcher import OCRDispatcher

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
def get_job_status(
    job_id: str,
    dispatcher: OCRDispatcher = Depends(get_ocr_dispatcher),
    audit: AuditService = Depends(get_audit_service),
) -> dict:
    job = dispatcher.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job": job,
        "audit_logs": audit.list_for_job(job_id),
    }
