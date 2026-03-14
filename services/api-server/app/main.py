from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as documents_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.norm_library import router as norm_library_router
from app.api.routes.norms import router as norms_router
from app.api.routes.norm_search import router as norm_search_router
from app.api.routes.project_ai_settings import router as project_ai_settings_router
from app.api.routes.projects import router as projects_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3010",
        "http://127.0.0.1:3010",
        "http://localhost:3011",
        "http://127.0.0.1:3011",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(jobs_router)
app.include_router(norm_library_router)
app.include_router(norms_router)
app.include_router(norm_search_router)
app.include_router(projects_router)
app.include_router(project_ai_settings_router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
