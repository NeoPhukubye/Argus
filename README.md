# ArgusCode

ArgusCode evaluates a codebase in **self-check** mode (your personal bar) or **reviewer** mode (independent audit for someone deciding whether to trust/merge/hire off it). Built for the micro1 Agentic Workflows Hackathon 2026.

## Who has this problem?

Engineers, reviewers, and engineering managers who need to judge whether a codebase is actually good before relying on it — shipping it, buying it, grading it, or hiring off it.

## What bottleneck makes it worth solving?

Reading a repo by hand doesn't scale and is inconsistent. A README and passing demo tell you almost nothing about test coverage, error handling, architecture, or technical debt. If you don't have a repeatable method, quality assessment depends on incomplete or inconsistent judgment.

## Does the agent solve it well?

Yes. ArgusCode clones and scans a repo, runs the build and tests, checks structure/dependencies/error-handling coverage, and scores it against a rubric with file:line evidence. The mutation-check verification layer catches the critical failure mode: passing tests that would not actually catch regressions. A qualified human still makes the final call.

## Can another person reproduce the result?

Yes. Use public repos, document exact setup/commands/tool versions, and tie every score to a file, test result, or build output. See `REPRODUCTION.md`.

## Rubric Dimensions

| Dimension | Weight | Verification |
|-----------|--------|--------------|
| build_setup_reproducibility | 20% | Exit code 0, env logs, dependency resolution time |
| test_quality_resilience | 25% | Test runner output, passed/failed, mutation check |
| error_handling_fault_tolerance | 20% | Bare except / catch-all scan, unhandled rejections, fallbacks |
| dependency_hygiene_security | 15% | Lockfile audit, outdated/vulnerable packages, license check |
| architectural_structure_docs | 20% | README command check, AST file graph, docstring coverage |

## Usage

### CLI

```bash
export GEMINI_API_KEY="your-key"
python argus/main.py https://github.com/neophukubye/TraceBot --mode reviewer
python argus/main.py /path/to/your/repo --mode self_check
python argus/main.py /path/to/your/repo --mode baseline
```

Outputs to `reports/latest.json` and `reports/latest.md`.

### Web

Frontend: GitHub Pages (static HTML/JS)  
Backend: Render.com (FastAPI)

```bash
cd web/backend
uvicorn main:app --reload
```

Open `web/frontend/index.html` or visit the GitHub Pages URL.

API: `POST /api/analyze` with `{ "repo": "<url>", "mode": "reviewer" }`

## Architecture

```
argus-code/
├── baseline/
│   └── run_baseline.py       # Direct LLM call (README + file tree -> 1-10 rating)
├── argus/
│   ├── core/
│   │   ├── scanner.py        # Cloner, AST parser, and file inspector
│   │   ├── runner.py         # Sandboxed build and test execution engine
│   │   └── verifier.py       # Test meaningfulness & mutation validation
│   ├── agents/
│   │   ├── evaluator.py      # Core evaluation logic against rubric dimensions
│   │   └── reporter.py       # Dual-mode report generator (Self-Check vs Reviewer)
│   ├── tools/
│   │   ├── static_tools.py   # Linters, AST analyzers, audit runners
│   │   └── dynamic_tools.py  # Subprocess sandbox executor
│   └── main.py               # CLI entrypoint
├── web/
│   ├── backend/              # FastAPI service (deploy to Render.com)
│   └── frontend/             # Static site (deploy to GitHub Pages)
├── eval/
│   ├── test_cases.json       # Metadata for 10+ evaluation repos
│   └── benchmark.py          # Baseline vs Argus comparison runner
├── trajectories/             # Exported agent reasoning + tool call traces
├── CHANGELOG.md
├── REPRODUCTION.md
└── README.md
```

## Baseline vs Advanced

| | Baseline | Advanced |
|--|----------|----------|
| Input | README + file tree | Full scan + pytest/coverage + static/dynamic tools |
| Tool use | None | Sandboxed subprocess, AST, secrets scan, mutation check |
| Evidence | Free text | File:line citations per check |
| Modes | Rating only | Self-check + reviewer |
| LLM | Gemini 2.0 Flash | Gemini 2.0 Flash |

## Requirements

- Python 3.11+
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- git, pytest, coverage installed

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[web]"
```

**Note:** `pip install -e .` is required before installing web backend deps, because `web/backend/` imports from the root `argus/` package.

## License

MIT
