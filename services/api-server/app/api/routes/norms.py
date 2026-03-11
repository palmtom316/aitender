from fastapi import APIRouter
from pydantic import BaseModel

from app.services.norm_index_builder import NormIndexBuilder

router = APIRouter(prefix="/norms", tags=["norms"])


class NormIndexPreviewRequest(BaseModel):
    document_id: str
    markdown_text: str
    page_texts: list[dict]


@router.post("/index-preview")
def preview_norm_index(payload: NormIndexPreviewRequest) -> dict:
    return NormIndexBuilder().build(
        document_id=payload.document_id,
        markdown_text=payload.markdown_text,
        page_texts=payload.page_texts,
    )
