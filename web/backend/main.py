from pathlib import Path
from typing import Optional
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from .middleware import RateLimitMiddleware

app = FastAPI(title="ArgusCode API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.onrender.com",
    ],
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, requests_per_minute=30)

from .routes.analyze import router as analyze_router
from .routes.health import router as health_router

app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(analyze_router, prefix="/api/analyze", tags=["Analyze"])

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/{full_path:path}")
def serve_frontend(request: Request, full_path: str):
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    path = FRONTEND_DIR / full_path
    if full_path and path.exists() and path.is_file():
        return FileResponse(path)
    return FileResponse(FRONTEND_DIR / "index.html")
