#!/usr/bin/env python3
"""ArgusCode CLI entrypoint."""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

from argus.agents.evaluator import Evaluator
from argus.agents.reporter import Reporter
from argus.core.scanner import clone_repo
from argus.types import RepoReport


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    ap = argparse.ArgumentParser(description="ArgusCode — agentic code review")
    ap.add_argument("repo", help="Local repo path or git URL")
    ap.add_argument("--mode", choices=["self_check", "reviewer", "baseline"], default="reviewer")
    ap.add_argument("--model", default="gemini-2.0-flash")
    ap.add_argument("--output", default="reports/latest.json")
    ap.add_argument("--md", default="reports/latest.md")
    args = ap.parse_args()

    repo_path = Path(args.repo)
    if "://" in args.repo or args.repo.count("/") == 1:
        dest = Path("/tmp") / args.repo.replace("/", "_").replace(":", "_")
        repo_path = clone_repo(args.repo, dest)

    if args.mode == "baseline":
        from baseline.run_baseline import run_baseline
        report = run_baseline(repo_path, model=args.model)
    else:
        evaluator = Evaluator(repo_path, mode=args.mode)
        report = evaluator.score()

    out_json = Path(args.output)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    reporter = Reporter(report)
    out_json.write_text(json.dumps(reporter.to_json(), indent=2))

    out_md = Path(args.md)
    out_md.write_text(reporter.to_markdown())

    print(f"Wrote {out_json} (score={report.overall_score:.2f})")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
