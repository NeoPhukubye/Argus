import json
import logging
import shutil
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import tomli as tomllib

from argus.types import ToolCall, Trajectory

log = logging.getLogger(__name__)


def clone_repo(url: str, dest: Path, timeout: int = 120) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    log.info("cloning", extra={"url": url, "dest": str(dest)})
    subprocess.check_output(
        ["git", "clone", "--depth=1", url, str(dest)],
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
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
    except (OSError, UnicodeDecodeError) as exc:
        log.debug("read_failed", extra={"path": str(path), "error": str(exc)})
        return ""


def toml_load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        data: dict[str, Any] = tomllib.load(f)
    return data


def json_load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data: dict[str, Any] = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return data


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
    except (subprocess.SubprocessError, OSError) as exc:
        return {"ok": False, "output": str(exc), "duration_ms": int((time.perf_counter() - start) * 1000)}


class SandboxedRunner:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.trajectory = Trajectory(repo=repo_path.name, mode="", tool_calls=[], prompts=[])

    def run(self, tool_name: str, args: dict[str, Any], func: Callable[[], Any]) -> dict[str, Any]:
        call = ToolCall(tool=tool_name, args=args, result={}, duration_ms=0.0)
        start = time.perf_counter()
        try:
            call.result = func()
        except (subprocess.SubprocessError, OSError, ValueError) as exc:
            call.result = {"error": str(exc)}
        call.duration_ms = int((time.perf_counter() - start) * 1000)
        self.trajectory.tool_calls.append(call)
        return call.result
