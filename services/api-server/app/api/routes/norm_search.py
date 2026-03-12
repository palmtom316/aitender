from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.norm_search_service import norm_search_service

router = APIRouter(prefix="/norm-search", tags=["norm-search"])


class NormSearchRequest(BaseModel):
    document_id: str
    clause_index: dict | None = None
    commentary_result: dict | None = None
    query: str | None = None
    clause_id: str | None = None
    path_prefix: str | None = None


@router.post("/query")
def query_norm(payload: NormSearchRequest) -> dict:
    if payload.clause_index is None or payload.commentary_result is None:
        result = norm_search_service.search_document(
            document_id=payload.document_id,
            query=payload.query,
            clause_id=payload.clause_id,
            path_prefix=payload.path_prefix,
        )
        if result is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "clause_index and commentary_result are required unless the "
                    "repository backend provides persisted norm search data"
                ),
            )
        return result

    return norm_search_service.search(
        document_id=payload.document_id,
        clause_index=payload.clause_index,
        commentary_result=payload.commentary_result,
        query=payload.query,
        clause_id=payload.clause_id,
        path_prefix=payload.path_prefix,
    )
