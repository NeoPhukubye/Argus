import ast
import logging
from pathlib import Path
from typing import Any

from argus.core.scanner import find_files, safe_read

log = logging.getLogger(__name__)


class Verifier:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    def bare_except_count(self) -> dict[str, Any]:
        hits: list[str] = []
        for p in find_files(self.repo_path, ["*.py"]):
            try:
                text = p.read_text(errors="ignore").splitlines()
                for i, line in enumerate(text, 1):
                    if line.strip() == "except:":
                        hits.append(f"{p.relative_to(self.repo_path)}:{i}")
            except Exception:
                continue
        return {"count": len(hits), "hits": hits[:20]}

    def ast_bare_except_count(self) -> dict[str, Any]:
        hits: list[str] = []
        for p in find_files(self.repo_path, ["*.py"]):
            try:
                tree = ast.parse(p.read_text(errors="ignore"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler) and node.type is None:
                        hits.append(f"{p.relative_to(self.repo_path)}:{node.lineno}")
            except Exception:
                continue
        return {"count": len(hits), "hits": hits[:20]}

    def secrets_scan(self) -> dict[str, Any]:
        patterns = ["-----BEGIN", "api_key", "secret", "password", "token =", "Authorization"]
        hits: list[str] = []
        for p in find_files(self.repo_path, ["*"]):
            if not p.is_file() or any(s in str(p) for s in ["node_modules", ".git", "__pycache__"]):
                continue
            try:
                text = p.read_text(errors="ignore")[:200_000]
                for pat in patterns:
                    if pat in text:
                        hits.append(f"{p.relative_to(self.repo_path)}:{pat}")
                        break
            except Exception:
                continue
        return {"count": len(hits), "hits": hits[:20]}

    def large_files(self, threshold_bytes: int = 500_000) -> dict[str, Any]:
        files = find_files(self.repo_path, ["*"])
        hits = [str(p.relative_to(self.repo_path)) for p in files if p.is_file() and p.stat().st_size > threshold_bytes]
        return {"count": len(hits), "files": hits[:20]}

    def mutation_check(self) -> dict[str, Any]:
        pyproject = self.repo_path / "pyproject.toml"
        if not pyproject.exists():
            return {"supported": False, "reason": "no pyproject.toml"}
        src = find_files(self.repo_path, ["*.py"])
        src = [p for p in src if "test" not in str(p).lower() and "__pycache__" not in str(p)][:5]
        if not src:
            return {"supported": False, "reason": "no source files found"}
        import re
        error_handlers = 0
        for p in src:
            text = safe_read(p)
            if "except:" in text or "except Exception:" in text:
                error_handlers += 1
        return {
            "supported": True,
            "files_scanned": len(src),
            "files_with_error_handling": error_handlers,
            "mutation_surface": "replace error handling with pass and rerun tests",
        }
