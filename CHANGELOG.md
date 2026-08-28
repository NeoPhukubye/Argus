# Changelog

## 0.1.0 — 2026-08-28

- Initial scaffold: ArgusCode with Gemini 2.0 Flash.
- Rubric: 5 dimensions, weighted scoring, evidence-linked findings.
- Dual-mode output: self-check punch list vs reviewer audit report.
- Baseline harness: single-prompt LLM (README + file tree only).
- Eval harness: 10-repo test set + messy failure case.
- Tools: pytest, coverage, secrets scan, bare except scan, mutation check, docstring coverage, README command check, dependency audit.
- CLI entrypoint: `argus/main.py`.

## Planned (next 48h)

- Add architecture-smell heuristics (circular imports, import cycle graph).
- Video demo and reproduction guide.
- Expand test cases to 15+ with more public OSS diversity.
