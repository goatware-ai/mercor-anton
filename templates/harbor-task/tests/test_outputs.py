"""Deterministic gate for swe-smoke-002: the truncation repro flips, and nothing
the prompt froze has moved.

Only what the prompt states is tested here. The qualitative requirements (root
cause rather than symptom, reuse of _flush(), chunking preserved, how a short
export fails) are judged by annotators through the rubrics, because more than
one implementation satisfies the prompt and a test would have to pick one.
"""

import importlib.util
import inspect
from pathlib import Path

import pytest

EXPORTER = Path("/workspace/exporter.py")


@pytest.fixture
def exporter():
    assert EXPORTER.is_file(), f"{EXPORTER} was not created"
    spec = importlib.util.spec_from_file_location("exporter_under_test", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rows(n):
    return [(i, f"name-{i}", i * 1.5) for i in range(n)]


def expected_lines(n):
    return [f"{i},name-{i},{i * 1.5}" for i in range(n)]


@pytest.mark.parametrize("n", [1, 2, 3, 5, 6, 7, 9, 13])
def test_final_partial_chunk_is_written(exporter, tmp_path, n):
    out = tmp_path / "export.csv"
    exporter.export(rows(n), str(out))
    assert out.read_text().splitlines() == expected_lines(n)


@pytest.mark.parametrize("n", [4, 8, 16])
def test_exact_multiples_still_export(exporter, tmp_path, n):
    out = tmp_path / "export.csv"
    exporter.export(rows(n), str(out))
    assert out.read_text().splitlines() == expected_lines(n)


def test_export_returns_its_path(exporter, tmp_path):
    out = tmp_path / "export.csv"
    assert exporter.export(rows(3), str(out)) == str(out)


def test_public_signatures_unchanged(exporter):
    assert list(inspect.signature(exporter.export).parameters) == ["rows", "path"]
    write_row = inspect.signature(exporter.ChunkedCsvWriter.write_row)
    assert list(write_row.parameters) == ["self", "row"]


def test_flush_threshold_not_raised(exporter):
    assert exporter.ChunkedCsvWriter.FLUSH_THRESHOLD == 4
