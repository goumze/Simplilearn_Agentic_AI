from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env.local"))

app = FastAPI(title="SaaS API")


# ---------------------------------------------------------------------------
# API routes — add your endpoints here
# ---------------------------------------------------------------------------

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from FastAPI!"}


# ---------------------------------------------------------------------------
# Serve Next.js static export
# Must be mounted LAST so API routes take priority
# ---------------------------------------------------------------------------

_out_dir = os.path.join(os.path.dirname(__file__), "..", "out")

if os.path.isdir(_out_dir):
    app.mount("/", StaticFiles(directory=_out_dir, html=True), name="static")
