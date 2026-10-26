from pathlib import Path

from argus.core.scanner import detect_language, find_files, json_load, safe_read, toml_load


def test_safe_read_existing_file(tmp_path: Path) -> None:
    target = tmp_path / "hello.txt"
    target.write_text("hello world")
    assert safe_read(target) == "hello world"


def test_safe_read_missing_file(tmp_path: Path) -> None:
    assert safe_read(tmp_path / "nope.txt") == ""


def test_safe_read_truncates_large_file(tmp_path: Path) -> None:
    target = tmp_path / "big.txt"
    target.write_text("x" * 500_000)
    result = safe_read(target, max_bytes=1000)
    assert len(result) == 1000


def test_find_files(tmp_path: Path) -> None:
    (tmp_path / "a.py").touch()
    (tmp_path / "b.txt").touch()
    (tmp_path / "c.py").touch()
    results = find_files(tmp_path, ["*.py"])
    assert len(results) == 2
    assert all(p.suffix == ".py" for p in results)


def test_toml_load_existing(tmp_path: Path) -> None:
    target = tmp_path / "pyproject.toml"
    target.write_text('name = "foo"\nversion = "1.0"\n')
    data = toml_load(target)
    assert data["name"] == "foo"


def test_toml_load_missing(tmp_path: Path) -> None:
    assert toml_load(tmp_path / "missing.toml") == {}


def test_json_load_existing(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    target.write_text('{"key": "value"}')
    assert json_load(target) == {"key": "value"}


def test_json_load_missing(tmp_path: Path) -> None:
    assert json_load(tmp_path / "missing.json") == {}


def test_detect_language_python(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").touch()
    assert detect_language(tmp_path) == "python"


def test_detect_language_node(tmp_path: Path) -> None:
    (tmp_path / "package.json").touch()
    assert detect_language(tmp_path) == "node"


def test_detect_language_unknown(tmp_path: Path) -> None:
    assert detect_language(tmp_path) == "unknown"
