The requested dead code filtering and node detail capabilities have been implemented in the frontend components:

1. **Dead Code Filter & Counts (`FilterPanel`, `GraphTab`, `utils`):**
   - Added `isDeadNode` and `getDeadNodeIds` to detect unreachable functions (functions with no callers or marked dead).
   - Displayed the dead code count formatted as `"X dead"` next to the "Dead code" section header in `FilterPanel`.
   - Added a "Show only dead code" toggle button that filters visible nodes in `GraphTab` down to unreachable functions.
   - Preserved and displayed the "filtered from N" notice in the HUD when filtering is active.

2. **Node Source Code & GitHub Navigation (`NodeDetailPanel`, `utils`):**
   - Added a "Show code" button for nodes with code metadata that fetches source via `get_code_snippet` and renders it safely as literal text in a `<pre><code>` block without DOM interpretation.
   - Added an "Open on GitHub" link displayed when the git remote is known, encoding special characters in the file path (`@`, spaces, etc.), attaching line anchors (`#Lstart-Lend` or `#Lstart`), and setting `target="_blank"` with `rel="noopener noreferrer"`.
