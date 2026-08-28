import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from argus.core.scanner import clone_repo, detect_language, find_files, run_command, safe_read, toml_load
from argus.types import ToolCall, Trajectory

log = logging.getLogger(__name__)


class RepoRunner:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.language = detect_language(repo_path)
        self.trajectory = Trajectory(repo=repo_path.name, mode="", tool_calls=[], prompts=[])

    def run(self, tool_name: str, args: dict[str, Any], func) -> dict[str, Any]:
        call = ToolCall(tool=tool_name, args=args, result={}, duration_ms=0.0)
        start = time.perf_counter()
        try:
            call.result = func()
        except Exception as exc:
            call.result = {"error": str(exc)}
        call.duration_ms = int((time.perf_counter() - start) * 1000)
        self.trajectory.tool_calls.append(call)
        return call.result

    def build(self) -> dict[str, Any]:
        if self.language == "python":
            return self.run("build", {"cmd": "pip install -e . || pip install . || true"}, lambda: run_command("pip install -e . || pip install . || true", self.repo_path))
        if self.language == "node":
            return self.run("build", {"cmd": "npm ci || npm install"}, lambda: run_command("npm ci || npm install", self.repo_path))
        return self.run("build", {"cmd": "echo 'no build step detected'"}, lambda: {"ok": True, "output": "no build step detected"})

    def test(self) -> dict[str, Any]:
        if self.language == "python":
            return self.run("test", {"cmd": "pytest -q --tb=short --no-header || true"}, lambda: run_command("pytest -q --tb=short --no-header || true", self.repo_path))
        if self.language == "node":
            return self.run("test", {"cmd": "npm test || true"}, lambda: run_command("npm test || true", self.repo_path))
        return self.run("test", {"cmd": "echo 'no tests detected'"}, lambda: {"ok": True, "output": "no tests detected"})

    def coverage(self) -> dict[str, Any]:
        if self.language == "python":
            def _cov():
                run_command("python -m coverage run -m pytest -q --tb=short --no-header >/dev/null 2>&1 || true", self.repo_path)
                return run_command("python -m coverage report || true", self.repo_path)
            return self.run("coverage", {"cmd": "coverage run + report"}, _cov)
        return self.run("coverage", {"cmd": "echo 'coverage not supported for language'"}, lambda: {"ok": True, "output": "coverage not supported for language"})

    def audit_dependencies(self) -> dict[str, Any]:
        if self.language == "python":
            return self.run("audit", {"cmd": "pip-audit || true"}, lambda: run_command("pip-audit || true", self.repo_path))
        if self.language == "node":
            return self.run("audit", {"cmd": "npm audit || true"}, lambda: run_command("npm audit || true", self.repo_path))
        return self.run("audit", {"cmd": "echo 'no audit tool detected'"}, lambda: {"ok": True, "output": "no audit tool detected"})
