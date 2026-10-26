import json
import os
from pathlib import Path
from typing import Any

from argus.core.scanner import find_files, safe_read
from argus.types import RepoReport


def _client():
    try:
        import google.generativeai as genai
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY not set")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.0-flash")
    except Exception as exc:
        raise RuntimeError(f"Gemini client init failed: {exc}")


SYSTEM_PROMPT = (
    "You are a code reviewer. Given a repo's README and file tree, "
    "rate it 1-10. Be concise. Respond as JSON with fields score and reasoning."
)


def build_prompt(repo_path: Path) -> str:
    tree_files = find_files(repo_path, ["*"])
    tree = "\n".join(str(p.relative_to(repo_path)) for p in tree_files[:300])
    readme = safe_read(repo_path / "README.md") or safe_read(repo_path / "readme.md") or ""
    return (
        "README:\n" + readme[:4000] + "\n\n"
        "FILE TREE (first 300 entries):\n" + tree[:8000]
    )


def run_baseline(repo_path: Path, model: str = "gemini-2.0-flash") -> RepoReport:
    prompt = build_prompt(repo_path)
    model_client = _client()
    response = model_client.generate_content(
        f"{SYSTEM_PROMPT}\n\n{prompt}",
        generation_config={"response_mime_type": "application/json"},
    )
    raw = response.text or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"score": 0, "reasoning": raw[:200]}
    raw_score = data.get("score", data.get("rating", 0))
    try:
        score = min(10.0, max(0.0, float(raw_score)))
    except Exception:
        score = 0.0
    return RepoReport(
        repo=str(repo_path.name),
        mode="baseline",
        dimensions=[],
        overall_score=score,
        narrative=data.get("reasoning", data.get("narrative", "")),
        metadata={"model": model, "raw_response": raw},
    )
