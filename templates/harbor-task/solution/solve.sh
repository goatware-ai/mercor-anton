#!/bin/bash
# Golden solution. Follows the prompt's own order: create the production file,
# reproduce the bug with a failing test, fix it, and show the test passing.
#
#   exporter.py   __exit__ returned without flushing, so any final buffer shorter
#                 than FLUSH_THRESHOLD (4) was dropped. That is why large exports
#                 looked fine: only the last partial chunk was lost. The fix
#                 flushes on a clean exit through the existing _flush(), and
#                 raises IncompleteExportError when the rows written don't match
#                 the rows submitted, so a short file can't come back silently.
#
# Harbor runs this as the oracle agent. Helpers resolve relative to this script.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /workspace

cp "$HERE/original_exporter.py" exporter.py
cp "$HERE/test_exporter.py" test_exporter.py

if python3 -m pytest -q -p no:cacheprovider test_exporter.py; then
    echo "expected the reproduction to fail against the production code" >&2
    exit 1
fi

cp "$HERE/exporter.py" exporter.py
python3 -m pytest -q -p no:cacheprovider test_exporter.py
