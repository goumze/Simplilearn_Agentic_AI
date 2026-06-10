from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

# Load .env.local when present (local development). In Docker / Lambda the
# environment variables are injected at runtime, so this is a no-op there.
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_path):
    load_dotenv(dotenv_path=_env_path)

app = FastAPI(title="SaaS API")


# ---------------------------------------------------------------------------
# Health check — required by the Dockerfile HEALTHCHECK and ALB / ECS probes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# API routes — add your endpoints here
# ---------------------------------------------------------------------------

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from FastAPI!"}


# ---------------------------------------------------------------------------
# Serve Next.js static export
# In Docker  the static dir is ./static  (copied by Dockerfile)
# In local dev the static dir is ./out   (produced by `npm run build`)
# Override with the STATIC_DIR env var if needed.
# Must be mounted LAST so API routes take priority.
# ---------------------------------------------------------------------------

_static_dir = os.environ.get("STATIC_DIR")
if not _static_dir:
    # auto-detect: Docker path first, then local Next.js export path
    for _candidate in ["static", "out"]:
        if os.path.isdir(_candidate):
            _static_dir = _candidate
            break

if _static_dir and os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
