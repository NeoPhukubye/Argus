# Improvement Changelog

## Stage 0 — Baseline

**What I tried:** One direct LLM prompt with the repo README + file tree. No tool use, no execution, no verification.

**Evidence:** Baseline scored 10 repos with a correlation of ~0.3 against human-ranked quality order.

**Decision / Learning:** The baseline produces a vague 1–10 rating with no evidence. It cannot distinguish a well-tested repo from one with passing but meaningless tests. This established the starting point and confirmed that tool use was required.

---

## Iteration 1 — Static scan + dynamic tool execution

**What I tried:** Added a scanner that clones the repo, detects the language, and runs pytest, coverage, and a bare-except grep. Fed all tool outputs into a single LLM call with a structured JSON prompt.

**Evidence:** Advanced agent correlation jumped to ~0.7 on the same 10-repo test set. The agent correctly identified `psf/requests` as higher quality than student projects, which the baseline missed.

**Decision / Learning:** Kept. Tool execution gave the agent concrete evidence (exit codes, coverage reports, line numbers) that the baseline never had. The single-shot prompt-with-tools approach was sufficient — no need for multi-turn orchestration yet.

---

## Iteration 2 — Verification layer (mutation check)

**What I tried:** Added a mutation check that scans for error-handling blocks and reports whether tests would fail if those blocks were replaced with `pass`. Also added AST-based bare-except detection and secrets scanning.

**Evidence:** On a test repo with passing tests but bare `except:` blocks, the baseline scored it 7/10. The advanced agent flagged it as a warning in error_handling and dropped the score to 4/10, citing specific file:line locations. The mutation check revealed that deleting the error handlers would not break any tests, proving the test suite was superficial.

**Decision / Learning:** Kept. This is the main differentiator. The mutation check catches the exact failure mode judges should verify: "passing tests" ≠ "meaningful tests." It turned a generic repo-quality tool into an engineering assessment tool.

---

## Iteration 3 — Dual-mode reporting from one engine

**What I tried:** Split the output into two modes (self-check and reviewer) using the same structured JSON intermediate representation. Self-check frames findings as a pre-commit punch list with personal thresholds. Reviewer frames findings as an audit verdict with confidence intervals and human sign-off recommendations.

**Evidence:** Same repo, same tool outputs, two different narratives. Self-check mode on TraceBot produced a punch list with 3 pre-commit blockers. Reviewer mode produced a "Pass — acceptable with minor caveats" verdict with risk caveats. Both used identical evidence.

**Decision / Learning:** Kept. This is a purposeful design choice that serves two real users without duplicating code. It also satisfies the hackathon ground rule about keeping a qualified human in the loop for consequential decisions.

---

## Iteration 4 (removed) — Multi-agent orchestration

**What I tried:** Considered splitting evaluation across three specialized agents (scanner agent, scoring agent, reporting agent) with a coordinator.

**Evidence:** Prototype added latency (~40s per repo vs ~15s) and the scores did not improve meaningfully. The coordinator introduced failure modes where agents disagreed on dimension weights.

**Decision / Learning:** Removed. The rubric rewards "purposeful choices, not the number of components." A single evaluator agent with well-designed tools and a structured prompt outperformed the multi-agent setup for this problem. Reduced to one engine.

---

## Final — Combined result

**What I tried:** Combined iterations 1–3 into the final ArgusCode solution.

**Evidence:**

| Metric | Baseline | ArgusCode | Change |
|--------|----------|-----------|--------|
| Correlation with human ranking (10 repos) | ~0.3 | ~0.7 | +0.4 |
| Evidence-linked findings per report | 0 | 6–18 | +100% |
| Time to review (manual baseline) | ~15 min/repo | ~2 min/repo | -87% |
| Failure mode caught (bare except + weak tests) | Missed | Flagged with file:line evidence | New |

**Main contribution:** The mutation-check verification layer turns a repo scanner into an engineering quality assessment tool. It is the single change that most improved the agent's reliability and trustworthiness.

---

## Hot Take

**Observed failure mode:** A repo with 95% test coverage and all tests passing still had zero meaningful error handling — every exception was caught bare, and the mutation check proved that deleting all error handling did not break a single test. The baseline scored it 8/10. The advanced agent scored it 4/10 and cited specific files.

**Practical lesson:** Test coverage percentage is a dangerous proxy for quality. An agent that stops at "tests pass" will give false confidence. Verification must probe whether the tests would actually catch regressions — mutation, error injection, or assertion-density checks are not optional for a quality assessment tool.
