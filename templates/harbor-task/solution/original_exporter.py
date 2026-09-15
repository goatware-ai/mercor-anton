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
