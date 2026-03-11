# aitender

Task 1 scaffold for the tender library MVP.

## Structure

- `apps/web`: Next.js web shell with a minimal homepage test
- `services/api-server`: FastAPI shell with a minimal health-check test
- `workers/document-worker`: placeholder for background processing
- `packages/shared`: placeholder for cross-project shared code
- `docs`: planning and product documents

## Quick Start

### Web

```bash
cd apps/web
npm install
npm test
```

### API

```bash
python3 -m venv .venv
.venv/bin/pip install fastapi==0.116.1 uvicorn==0.35.0 httpx==0.28.1 pytest==8.3.5
PYTHONPATH=services/api-server .venv/bin/pytest services/api-server/tests/test_health.py -q
```
