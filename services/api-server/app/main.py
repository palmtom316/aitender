from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as documents_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.norms import router as norms_router
from app.api.routes.norm_search import router as norm_search_router
from app.api.routes.projects import router as projects_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(jobs_router)
app.include_router(norms_router)
app.include_router(norm_search_router)
app.include_router(projects_router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
