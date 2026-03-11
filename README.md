# aitender

Tender library Phase 1 MVP for规范规程 PDF upload, processing, search, and preview.

## Structure

- `apps/web`: Next.js UI for login, projects, norm library search, status, and preview
- `services/api-server`: FastAPI API for auth, uploads, OCR jobs, norm indexing, search, and job status
- `workers/document-worker`: document processing entrypoint
- `packages/shared`: shared package placeholder
- `docs`: planning, product, and workflow documents

## Quick Start

### Web

```bash
cd apps/web
npm install
npm test -- --runInBand
npm run test:e2e
npm run build
```

### API

```bash
python3 -m venv .venv
.venv/bin/pip install fastapi==0.116.1 uvicorn==0.35.0 httpx==0.28.1 pytest==8.3.5 python-multipart==0.0.20
PYTHONPATH=services/api-server .venv/bin/pytest services/api-server/tests -q
PYTHONPATH=services/api-server .venv/bin/pytest services/api-server/tests/test_norm_pipeline_e2e.py -q
```

## Current MVP

- Upload norm PDF into a project-scoped library
- Track OCR processing jobs and audit steps
- Build norm clause indexes and commentary mappings
- Search clauses by keyword and inspect detail/highlight previews
- Exercise a lightweight web E2E flow with `npm run test:e2e`
