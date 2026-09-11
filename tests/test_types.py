from argus.types import (
    DimensionScore,
    Finding,
    RepoReport,
    Rubric,
    RubricCheck,
    RubricDimension,
    ToolCall,
    Trajectory,
)


def test_finding_defaults() -> None:
    f = Finding(
        check_id="SEC-001",
        dimension="Security",
        passed=True,
        evidence="no secrets found",
        points_awarded=1,
        points_possible=1,
    )
    assert f.check_id == "SEC-001"
    assert f.passed is True


def test_dimension_score() -> None:
    d = DimensionScore(name="Security", weight=0.2, score=0.9)
    assert d.findings == []


def test_repo_report() -> None:
    r = RepoReport(
        repo="test-repo",
        mode="reviewer",
        dimensions=[],
        overall_score=0.85,
    )
    assert r.narrative == ""
    assert r.metadata == {}


def test_rubric_check() -> None:
    c = RubricCheck(check_id="COR-001", description="No bare except")
    assert c.weight == 1.0


def test_rubric_dimension() -> None:
    d = RubricDimension(name="Correctness", weight=0.2)
    assert d.checks == []


def test_rubric() -> None:
    r = Rubric(name="standard", dimensions=[])
    assert r.dimensions == []


def test_tool_call() -> None:
    t = ToolCall(tool="build", args={}, result={"ok": True})
    assert t.duration_ms == 0.0


def test_trajectory() -> None:
    t = Trajectory(repo="test", mode="reviewer", tool_calls=[], prompts=[])
    assert t.raw_response == ""
