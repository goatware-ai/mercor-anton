import pytest

import exporter


@pytest.mark.parametrize("n", [1, 5, 7])
def test_tail_below_threshold_is_written(tmp_path, n):
    out = tmp_path / "out.csv"
    exporter.export([(i, f"r{i}") for i in range(n)], str(out))
    assert out.read_text().splitlines() == [f"{i},r{i}" for i in range(n)]


def test_short_write_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter.ChunkedCsvWriter, "_flush", lambda self: None)
    with pytest.raises(Exception):
        exporter.export([(1,), (2,)], str(tmp_path / "out.csv"))
