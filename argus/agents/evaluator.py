import json
import logging
import os
import re
from pathlib import Path
from textwrap import dedent
from typing import Any

from argus.core.scanner import detect_language, find_files, safe_read, toml_load
from argus.core.verifier import Verifier
from argus.tools.dynamic_tools import DynamicTools
from argus.tools.static_tools import StaticTools
from argus.types import DimensionScore, Finding, RepoReport

log = logging.getLogger(__name__)


SYSTEM_PROMPT = dedent(
    """
    You are ArgusCode, a deterministic code-review agent.
    You have scan results, static analysis, and dynamic tool outputs.
    Produce only JSON matching this schema:
    {
      "dimensions": [
        {
          "name": "<dimension>",
          "score": <0-1>,
          "findings": [
            {"check_id": "<id>", "passed": true/false, "evidence": "<short text>"}
          ]
        }
      ],
      "overall_score": <0-1>,
      "narrative": "<2-3 sentence summary>"
    }
    """
)


class Evaluator:
    def __init__(self, repo_path: Path, mode: str = "reviewer"):
        self.repo_path = repo_path
        self.mode = mode
        self.language = detect_language(repo_path)
        self.verifier = Verifier(repo_path)
        self.static = StaticTools(repo_path)
        self.dynamic = DynamicTools(repo_path)
        self.trajectory = self.dynamic.runner.trajectory

    def _client(self):
        try:
            import google.generativeai as genai
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY not set")
            genai.configure(api_key=api_key)
            return genai.GenerativeModel("gemini-2.0-flash")
        except Exception as exc:
            log.error("gemini_client_failed", error=str(exc))
            raise

    def scan(self) -> dict[str, Any]:
        pyproject = toml_load(self.repo_path / "pyproject.toml")
        pkg = {}
        pkg_path = self.repo_path / "package.json"
        if pkg_path.exists():
            try:
                pkg = json.loads(pkg_path.read_text())
            except Exception:
                pass
        tests = find_files(self.repo_path, [
            "tests/**/*.py", "test/**/*.py", "__tests__/**/*.py",
            "tests/**/*.ts", "test/**/*.ts"
        ])
        sources = find_files(self.repo_path, ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx"])
        sources = [p for p in sources if "node_modules" not in str(p) and "__pycache__" not in str(p)]
        try:
            import git
            repo_obj = git.Repo(self.repo_path)
            commit_count = int(repo_obj.git.rev_list("--count", "HEAD"))
        except Exception:
            commit_count = 0
        return {
            "repo": self.repo_path.name,
            "commit_count": commit_count,
            "language": self.language,
            "pyproject": {k: pyproject.get(k) for k in ["name", "version", "dependencies", "scripts"]},
            "package_json": {k: pkg.get(k) for k in ["name", "version", "dependencies", "scripts"]},
            "test_file_count": len(tests),
            "source_file_count": len(sources),
            "top_level_tree": sorted(str(p.relative_to(self.repo_path)) for p in list(self.repo_path.iterdir())[:40]),
        }

    def run_tools(self) -> dict[str, Any]:
        dynamic = self.dynamic.all()
        verifier = {
            "bare_except": self.verifier.bare_except_count(),
            "ast_bare_except": self.verifier.ast_bare_except_count(),
            "secrets": self.verifier.secrets_scan(),
            "large_files": self.verifier.large_files(),
            "mutation_check": self.verifier.mutation_check(),
        }
        static = {
            "docstring_coverage": self.static.docstring_coverage(),
            "readme_check": self.static.readme_command_check(),
            "deps": self.static.dependency_audit(),
            "coupling": self.static.module_coupling(),
        }
        return {"dynamic": dynamic, "verifier": verifier, "static": static}

    def build_prompt(self, scan: dict[str, Any], tools: dict[str, Any]) -> str:
        mode_prompt = {
            "self_check": "You are reviewing your own work before you sign your name to it. Be strict. Flag anything below your personal bar. Output is a punch list: PASS, WARN, or FAIL per dimension with specific file:line evidence.",
            "reviewer": "You are an independent code reviewer assessing whether this repo is ready to be trusted by others. Output a verdict per dimension with confidence and caveats. A human reviewer makes the final call.",
            "baseline": "You are a quick code reviewer. Given README and file tree, rate 1-10.",
        }.get(self.mode, "You are a code reviewer.")
        payload = {"mode": self.mode, "mode_prompt": mode_prompt, "scan": scan, "tools": tools}
        self.trajectory.prompts.append({"role": "user", "content": json.dumps(payload, indent=2)[:20000]})
        return json.dumps(payload, indent=2)[:20000]

    def score(self) -> RepoReport:
        scan = self.scan()
        tools = self.run_tools()
        prompt = self.build_prompt(scan, tools)
        model = self._client()
        self.trajectory.prompts.append({"role": "system", "content": SYSTEM_PROMPT})
        try:
            response = model.generate_content(
                f"{SYSTEM_PROMPT}\n\n{prompt}",
                generation_config={"response_mime_type": "application/json"},
            )
            raw = response.text or "{}"
        except Exception as exc:
            log.error("gemini_generate_failed", error=str(exc))
            raw = "{}"
        self.trajectory.raw_response = raw
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}
        dims: list[DimensionScore] = []
        for d in data.get("dimensions", []):
            dims.append(DimensionScore(
                name=str(d.get("name", "unknown")),
                weight=0.0,
                score=float(d.get("score", 0.0)),
                findings=[Finding(
                    check_id=f.get("check_id", "unknown"),
                    dimension=str(d.get("name", "unknown")),
                    passed=bool(f.get("passed", False)),
                    evidence=str(f.get("evidence", ""))[:300],
                    points_awarded=1 if f.get("passed") else 0,
                    points_possible=1,
                ) for f in d.get("findings", [])],
            ))
        overall = float(data.get("overall_score", 0.0))
        report = RepoReport(
            repo=scan.get("repo", str(self.repo_path.name)),
            mode=self.mode,
            dimensions=dims,
            overall_score=overall,
            narrative=data.get("narrative", ""),
            metadata={"scan": scan, "tools": tools, "model": "gemini-2.0-flash", "raw_response": raw},
        )
        self._save_trajectory(report)
        return report

    def _save_trajectory(self, report: RepoReport) -> None:
        try:
            import json
            from datetime import datetime
            out = Path("trajectories") / f"{report.repo}_{self.mode}.json"
            out.parent.mkdir(exist_ok=True)
            out.write_text(json.dumps({
                "repo": report.repo,
                "mode": self.mode,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "tool_calls": [
                    {
                        "tool": tc.tool,
                        "args": tc.args,
                        "result": tc.result,
                        "duration_ms": tc.duration_ms,
                    }
                    for tc in self.trajectory.tool_calls
                ],
                "prompts": self.trajectory.prompts,
                "raw_response": self.trajectory.raw_response,
                "overall_score": report.overall_score,
            }, indent=2))
        except Exception as exc:
            log.warning("trajectory_save_failed", error=str(exc))
