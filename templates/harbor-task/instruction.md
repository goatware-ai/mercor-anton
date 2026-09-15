Work entirely inside /workspace. You have a shell with Python; you have no internet access.

Create `exporter.py` containing exactly this implementation, which is currently in production:

```python
class ChunkedCsvWriter:
    FLUSH_THRESHOLD = 4

    def __init__(self, path):
        self.path = path
        self._buf = []
        self._rows_written = 0

    def write_row(self, row):
        self._buf.append(",".join(str(c) for c in row))
        if len(self._buf) >= self.FLUSH_THRESHOLD:
            self._flush()

    def _flush(self):
        if not self._buf:
            return
        with open(self.path, "a") as fh:
            fh.write("\n".join(self._buf) + "\n")
        self._rows_written += len(self._buf)
        self._buf = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def export(rows, path):
    with ChunkedCsvWriter(path) as w:
        for r in rows:
            w.write_row(r)
    return path
```

Users report that exports occasionally come back truncated, with no error raised. It does not
reproduce on large datasets.

Your job:
1. Write a test that reproduces the truncation and fails against the code above.
2. Fix the root cause.
3. Re-run the test and show it passing.

Constraints:
- Do NOT change the public signature of `export(rows, path)` or `ChunkedCsvWriter.write_row(row)`.
- Do NOT raise `FLUSH_THRESHOLD` or add a retry to mask the problem.
- A partial export must fail loudly rather than silently return a short file.

Finish with a short summary of the root cause and what you changed.
