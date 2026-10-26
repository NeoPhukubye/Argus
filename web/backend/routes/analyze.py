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
    expected_narrative: str | None = None


class AnalyzeResponse(BaseModel):
    repo: str
    mode: str
    rubric: str
    overall_score: float
    narrative: str
    narrative_match: float | None = None
    dimensions: list[dict]
    markdown: str


@router.post("/", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if not req.repo.strip():
        raise HTTPException(status_code=400, detail="Repository URL cannot be empty")
    dest = Path(f"/tmp/{req.repo.replace('/', '_').replace(':', '_')}")
    repo_path = clone_repo(req.repo, dest)
    evaluator = Evaluator(
        repo_path,
        mode=req.mode,
        rubric=get_rubric(req.rubric),
        expected_narrative=req.expected_narrative,
    )
    report = evaluator.score()
    reporter = Reporter(report)
    md = reporter.to_markdown()
    return AnalyzeResponse(
        repo=report.repo,
        mode=report.mode,
        rubric=req.rubric,
        overall_score=report.overall_score,
        narrative=report.narrative,
        narrative_match=report.metadata.get("narrative_match"),
        dimensions=[
            {
                "name": d.name,
                "weight": d.weight,
                "score": d.score,
                "findings": [
                    {"check_id": f.check_id, "passed": f.passed, "evidence": f.evidence,
                     "points_awarded": f.points_awarded, "points_possible": f.points_possible}
                    for f in d.findings
                ],
            }
            for d in report.dimensions
        ],
        markdown=md,
    )
