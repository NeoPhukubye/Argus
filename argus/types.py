from dataclasses import dataclass, field
from typing import Any


@dataclass
class Finding:
    check_id: str
    dimension: str
    passed: bool
    evidence: str
    points_awarded: int
    points_possible: int


@dataclass
class DimensionScore:
    name: str
    weight: float
    score: float
    findings: list[Finding] = field(default_factory=list)


@dataclass
class RepoReport:
    repo: str
    mode: str
    dimensions: list[DimensionScore]
    overall_score: float
    narrative: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalCase:
    repo: str
    expected_rank: int
    notes: str = ""


@dataclass
class ToolCall:
    tool: str
    args: dict[str, Any]
    result: dict[str, Any]
    duration_ms: float = 0.0


@dataclass
class Trajectory:
    repo: str
    mode: str
    tool_calls: list[ToolCall]
    prompts: list[dict[str, Any]]
    raw_response: str = ""


@dataclass
class RubricCheck:
    check_id: str
    description: str
    weight: float = 1.0


@dataclass
class RubricDimension:
    name: str
    weight: float
    checks: list[RubricCheck] = field(default_factory=list)


@dataclass
class Rubric:
    name: str
    dimensions: list[RubricDimension]
