from pathlib import Path

from argus.core.verifier import Verifier


def test_bare_except_count(tmp_path: Path) -> None:
    src = tmp_path / "mod.py"
    src.write_text("def foo():\n    try:\n        pass\n    except:\n        pass\n")
    v = Verifier(tmp_path)
    result = v.bare_except_count()
    assert result["count"] == 1


def test_ast_bare_except_count(tmp_path: Path) -> None:
    src = tmp_path / "mod.py"
    src.write_text("def foo():\n    try:\n        pass\n    except:\n        pass\n")
    v = Verifier(tmp_path)
    result = v.ast_bare_except_count()
    assert result["count"] == 1


def test_secrets_scan_detects_secret(tmp_path: Path) -> None:
    src = tmp_path / "config.py"
    src.write_text('api_key = "abc123"\n')
    v = Verifier(tmp_path)
    result = v.secrets_scan()
    assert result["count"] >= 1


def test_large_files(tmp_path: Path) -> None:
    big = tmp_path / "big.bin"
    big.write_bytes(b"x" * 600_000)
    small = tmp_path / "small.txt"
    small.write_text("hello")
    v = Verifier(tmp_path)
    result = v.large_files(threshold_bytes=500_000)
    assert result["count"] == 1
    assert "big.bin" in result["files"][0]


def test_mutation_check_no_pyproject(tmp_path: Path) -> None:
    v = Verifier(tmp_path)
    result = v.mutation_check()
    assert result["supported"] is False
    assert result["reason"] == "no pyproject.toml"
