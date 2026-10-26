import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import git

from argus.types import ToolCall, Trajectory

log = logging.getLogger(__name__)


def clone_repo(url: str, dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    log.info("cloning", url=url, dest=str(dest))
    git.Repo.clone_from(url, dest)
    return dest


def find_files(root: Path, patterns: list[str]) -> list[Path]:
    hits: list[Path] = []
    for pattern in patterns:
        hits.extend(root.rglob(pattern))
    return sorted(set(hits))


def safe_read(path: Path, max_bytes: int = 200_000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(errors="replace")[:max_bytes]
    except Exception as exc:
        log.debug("read_failed", path=str(path), error=str(exc))
        return ""


def toml_load(path: Path) -> dict[str, Any]:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def json_load(path: Path) -> dict[str, Any]:
    import json
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def detect_language(repo_path: Path) -> str:
    if (repo_path / "pyproject.toml").exists() or (repo_path / "setup.py").exists():
        return "python"
    if (repo_path / "package.json").exists():
        return "node"
    if (repo_path / "Cargo.toml").exists():
        return "rust"
    if (repo_path / "go.mod").exists():
        return "go"
    return "unknown"


def run_command(cmd: str, cwd: Path, timeout: int = 120) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        out = subprocess.check_output(
            cmd, shell=True, cwd=cwd, stderr=subprocess.STDOUT, timeout=timeout
        ).decode(errors="replace")
        return {"ok": True, "output": out[-8000:], "duration_ms": int((time.perf_counter() - start) * 1000)}
    except subprocess.CalledProcessError as exc:
        return {"ok": False, "output": exc.output.decode(errors="replace")[-8000:], "duration_ms": int((time.perf_counter() - start) * 1000)}
    except Exception as exc:
        return {"ok": False, "output": str(exc), "duration_ms": int((time.perf_counter() - start) * 1000)}


class SandboxedRunner:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
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
