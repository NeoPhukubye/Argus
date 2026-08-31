from argus.types import Rubric, RubricCheck, RubricDimension

STANDARD_RUBRIC = Rubric(
    name="standard",
    dimensions=[
        RubricDimension(
            name="Security",
            weight=0.20,
            checks=[
                RubricCheck("SEC-001", "No hardcoded secrets, API keys, or credentials"),
                RubricCheck("SEC-002", "No SQL injection vulnerabilities"),
                RubricCheck("SEC-003", "No unsafe deserialization"),
                RubricCheck("SEC-004", "No command injection risks"),
                RubricCheck("SEC-005", "Dependencies are reasonably up to date"),
            ],
        ),
        RubricDimension(
            name="Correctness",
            weight=0.20,
            checks=[
                RubricCheck("COR-001", "Error handling is explicit (no bare except)"),
                RubricCheck("COR-002", "Return values or exceptions are checked"),
                RubricCheck("COR-003", "Input validation is present"),
                RubricCheck("COR-004", "Tests cover non-trivial logic"),
                RubricCheck("COR-005", "No obviously broken edge cases"),
            ],
        ),
        RubricDimension(
            name="Maintainability",
            weight=0.15,
            checks=[
                RubricCheck("MTN-001", "Functions are reasonably small and cohesive"),
                RubricCheck("MTN-002", "Module coupling is low"),
                RubricCheck("MTN-003", "README is present and accurate"),
                RubricCheck("MTN-004", "Documentation covers non-obvious decisions"),
                RubricCheck("MTN-005", "Dependency surface is minimal"),
            ],
        ),
        RubricDimension(
            name="Performance",
            weight=0.15,
            checks=[
                RubricCheck("PER-001", "No obvious N+1 query or loop-in-loop patterns"),
                RubricCheck("PER-002", "Resource-intensive operations are bounded"),
                RubricCheck("PER-003", "No unnecessary eager loading of large data"),
                RubricCheck("PER-004", "Caching is used where appropriate"),
            ],
        ),
        RubricDimension(
            name="Reliability",
            weight=0.15,
            checks=[
                RubricCheck("REL-001", "Tests exist and are structured to run in CI"),
                RubricCheck("REL-002", "Error messages are actionable"),
                RubricCheck("REL-003", "Retry / circuit-breaker patterns for I/O"),
                RubricCheck("REL-004", "Graceful degradation on partial failure"),
            ],
        ),
        RubricDimension(
            name="Style",
            weight=0.15,
            checks=[
                RubricCheck("STL-001", "Code follows a consistent style"),
                RubricCheck("STL-002", "Naming is clear and consistent"),
                RubricCheck("STL-003", "No dead code or commented-out blocks"),
                RubricCheck("STL-004", "Imports are well-organized"),
            ],
        ),
    ],
)

RUBRICS: dict[str, Rubric] = {
    "standard": STANDARD_RUBRIC,
}


def get_rubric(name: str = "standard") -> Rubric:
    return RUBRICS.get(name, STANDARD_RUBRIC)
