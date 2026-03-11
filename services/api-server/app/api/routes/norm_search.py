from fastapi import APIRouter
from pydantic import BaseModel

from app.services.norm_search_service import norm_search_service

router = APIRouter(prefix="/norm-search", tags=["norm-search"])


class NormSearchRequest(BaseModel):
    document_id: str
    clause_index: dict
    commentary_result: dict
    query: str | None = None
    clause_id: str | None = None
    path_prefix: str | None = None


@router.post("/query")
def query_norm(payload: NormSearchRequest) -> dict:
    return norm_search_service.search(
        document_id=payload.document_id,
        clause_index=payload.clause_index,
        commentary_result=payload.commentary_result,
        query=payload.query,
        clause_id=payload.clause_id,
        path_prefix=payload.path_prefix,
    )
