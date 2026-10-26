# Reproduction Guide

## Prerequisites

1. Python 3.11+
2. Google AI API key (`GEMINI_API_KEY` or `GOOGLE_API_KEY`)
3. git, pytest, coverage installed

## Install (critical — do this in order)

```bash
python -m venv .venv
source .venv/bin/activate

# One-shot install: root package + web backend deps
pip install -e ".[web]"

# Or install separately:
# pip install -e .
# pip install -r web/backend/requirements.txt
```

**Why two installs?** `web/backend/` imports from the root `argus/` package. Installing `-e .` from the repo root makes `argus` importable everywhere. The `[web]` extra bundles both steps.

## Set API Key

```bash
export GEMINI_API_KEY="your-key"
# or
export GOOGLE_API_KEY="your-key"
```

## Run CLI

```bash
# Baseline
python baseline/run_baseline.py https://github.com/neophukubye/TraceBot --output reports/tracebot_baseline.json

# Advanced agent
python argus/main.py https://github.com/neophukubye/TraceBot --mode reviewer
python argus/main.py /path/to/your/repo --mode self_check
```

Outputs to `reports/latest.json` and `reports/latest.md`.

## Run Web Backend

```bash
cd web/backend
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`. Health check: `http://localhost:8000/api/health`.

## Run Full Benchmark

```bash
python eval/benchmark.py
```

This evaluates all 10 repos in both modes and writes `reports/benchmark.json` + `reports/benchmark.md`.

## Verify Evidence Traceability

Every finding in the JSON output includes `check_id` and `evidence`. Open the report and confirm each score maps to a real file, test, or tool output.

## What to Expect

- Baseline: fast, no tool use, vague narrative, 1-10 score only.
- Advanced: slower (clones + runs tests), structured rubric scores with file:line citations, two report modes.
