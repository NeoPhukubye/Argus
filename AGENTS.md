# ArgusCode

Quick rules for this repo:

- Python 3.11+, ruff style, types required.
- `argus/main.py` is the CLI entrypoint.
- `baseline/run_baseline.py` is the naive baseline.
- `eval/benchmark.py` runs the full eval (10 repos, baseline vs advanced).
- `reports/` is gitignored — write outputs there.
- Secrets go in `.env`, never committed.
- LLM: Google Gemini (`GEMINI_API_KEY` or `GOOGLE_API_KEY`).
