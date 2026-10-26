import logging
from pathlib import Path
from typing import Any

from argus.core.runner import RepoRunner
from argus.core.scanner import clone_repo
from argus.types import ToolCall, Trajectory

log = logging.getLogger(__name__)


class DynamicTools:
    def __init__(self, repo_path: Path):
        self.runner = RepoRunner(repo_path)

    def execute_tool(self, name: str, args: dict[str, Any], func) -> dict[str, Any]:
        return self.runner.run(name, args, func)

    def all(self) -> dict[str, Any]:
        build = self.runner.build()
        test = self.runner.test()
        coverage = self.runner.coverage()
        audit = self.runner.audit_dependencies()
        return {
            "build": build,
            "test": test,
            "coverage": coverage,
            "audit": audit,
        }
