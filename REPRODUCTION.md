# Reproduction Guide

## Prerequisites

1. Python 3.11+
2. Google AI API key (`GEMINI_API_KEY` or `GOOGLE_API_KEY`)
3. git, pytest, coverage, pip-audit installed

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Step 1: Set API Key

```bash
export GEMINI_API_KEY="your-key"
# or
export GOOGLE_API_KEY="your-key"
```

## Step 2: Run Baseline

```bash
python baseline/run_baseline.py https://github.com/neophukubye/TraceBot --output reports/tracebot_baseline.json
```

## Step 3: Run Advanced Agent (Reviewer Mode)

```bash
python argus/main.py https://github.com/neophukubye/TraceBot --mode reviewer
```

## Step 4: Run Advanced Agent (Self-Check Mode)

```bash
python argus/main.py /path/to/your/repo --mode self_check
```

## Step 5: Run Full Benchmark

```bash
python eval/benchmark.py
```

This evaluates all 10 repos in both modes and writes `reports/benchmark.json` + `reports/benchmark.md`.

## Step 6: Verify Evidence Traceability

Every finding in the JSON output includes `check_id` and `evidence`. Open the report and confirm each score maps to a real file, test, or tool output.

## What to Expect

- Baseline: fast, no tool use, vague narrative, 1-10 score only.
- Advanced: slower (clones + runs tests), structured rubric scores with file:line citations, two report modes.
