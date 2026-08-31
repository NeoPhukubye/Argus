from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from argus.agents.evaluator import Evaluator
from argus.agents.reporter import Reporter
from argus.core.scanner import clone_repo
from argus.rubric import get_rubric

router = APIRouter()


class AnalyzeRequest(BaseModel):
    repo: str
    mode: str = "reviewer"
    rubric: str = "standard"


class AnalyzeResponse(BaseModel):
    repo: str
    mode: str
    overall_score: float
    narrative: str
    dimensions: list[dict]
    markdown: str


@router.post("/", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if not req.repo.strip():
        raise HTTPException(status_code=400, detail="Repository URL cannot be empty")
    dest = Path(f"/tmp/{req.repo.replace('/', '_').replace(':', '_')}")
    repo_path = clone_repo(req.repo, dest)
    evaluator = Evaluator(repo_path, mode=req.mode, rubric=get_rubric(req.rubric))
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
