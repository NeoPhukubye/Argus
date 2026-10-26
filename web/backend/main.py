from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from argus.agents.evaluator import Evaluator
from argus.agents.reporter import Reporter
from argus.core.scanner import clone_repo

app = FastAPI(title="ArgusCode API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    repo: str
    mode: str = "reviewer"


class AnalyzeResponse(BaseModel):
    repo: str
    mode: str
    overall_score: float
    narrative: str
    dimensions: list[dict]
    markdown: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    try:
        dest = Path("/tmp") / req.repo.replace("/", "_").replace(":", "_")
        repo_path = clone_repo(req.repo, dest)
        evaluator = Evaluator(repo_path, mode=req.mode)
        report = evaluator.score()
        reporter = Reporter(report)
        md = reporter.to_markdown()
        return AnalyzeResponse(
            repo=report.repo,
            mode=report.mode,
            overall_score=report.overall_score,
            narrative=report.narrative,
            dimensions=[
                {
                    "name": d.name,
                    "score": d.score,
                    "findings": [
                        {"check_id": f.check_id, "passed": f.passed, "evidence": f.evidence}
                        for f in d.findings
                    ],
                }
                for d in report.dimensions
            ],
            markdown=md,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
