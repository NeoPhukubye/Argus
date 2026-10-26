import ast
import json
import logging
from pathlib import Path
from typing import Any

import tomli as tomllib

from argus.core.scanner import find_files, safe_read

log = logging.getLogger(__name__)


class StaticTools:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    def docstring_coverage(self) -> dict[str, Any]:
        sources = find_files(self.repo_path, ["*.py"])
        sources = [p for p in sources if "__pycache__" not in str(p)][:50]
        total = 0
        with_doc = 0
        for p in sources:
            try:
                tree = ast.parse(p.read_text(errors="ignore"))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        total += 1
                        if ast.get_docstring(node):
                            with_doc += 1
            except (OSError, SyntaxError) as exc:
                log.debug("parse_failed", extra={"path": str(p), "error": str(exc)})
                continue
        pct = (with_doc / total * 100) if total else 0.0
        return {"total": total, "with_docstring": with_doc, "coverage_pct": round(pct, 2)}

    def readme_command_check(self) -> dict[str, Any]:
        readme = safe_read(self.repo_path / "README.md") or safe_read(self.repo_path / "readme.md") or ""
        patterns = ["pip install", "npm install", "cargo build", "go build", "docker build", "make ", "just ", "poetry install"]
        found = [p for p in patterns if p.lower() in readme.lower()]
        return {"readme_present": bool(readme), "setup_commands_found": found, "count": len(found)}

    def dependency_audit(self) -> dict[str, Any]:
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            try:
                with pyproject.open("rb") as f:
                    data = tomllib.load(f)
                deps = data.get("project", {}).get("dependencies", []) or data.get("dependencies", [])
                return {"lockfile": "pyproject.toml", "dependency_count": len(deps), "dependencies": deps[:20]}
            except (OSError, tomllib.TOMLDecodeError) as exc:
                log.debug("toml_load_failed", extra={"path": str(pyproject), "error": str(exc)})
                return {"lockfile": "pyproject.toml", "dependency_count": 0, "dependencies": []}
        pkg = self.repo_path / "package.json"
        if pkg.exists():
            try:
                data = json.loads(pkg.read_text() or "{}")
            except (OSError, ValueError) as exc:
                log.debug("json_load_failed", extra={"path": str(pkg), "error": str(exc)})
                data = {}
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            return {"lockfile": "package.json", "dependency_count": len(deps), "dependencies": list(deps.keys())[:20]}
        return {"lockfile": None, "dependency_count": 0, "dependencies": []}

    def module_coupling(self) -> dict[str, Any]:
        sources = find_files(self.repo_path, ["*.py"])
        sources = [p for p in sources if "__pycache__" not in str(p)][:30]
        imports: dict[str, list[str]] = {}
        for p in sources:
            try:
                text = p.read_text(errors="ignore")
                tree = ast.parse(text)
                rel = str(p.relative_to(self.repo_path))
                imps = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        imps.append(node.module)
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            imps.append(alias.name)
                imports[rel] = imps[:20]
            except (OSError, SyntaxError) as exc:
                log.debug("parse_failed", extra={"path": str(p), "error": str(exc)})
                continue
        return {"files": len(imports), "imports": imports}
