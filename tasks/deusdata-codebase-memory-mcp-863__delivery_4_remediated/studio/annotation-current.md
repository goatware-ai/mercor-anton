# Current annotation: deusdata-codebase-memory-mcp-863__delivery_4_remediated#model_ab

The annotation as it stands in Studio at export time. Generated; don't edit.

## Trajectory A (gemini-3.7-flash)

**Dimension 0:** PARTIAL

### 2 · Architecture, Modularity & Trade-off Soundness: 3

isDeadNode/getDeadNodeIds in utils.ts is a clean, reusable module boundary, and the fallback path (compute dead status client-side from the edges already in GraphData when the server sends no is_dead flag) is a real design choice, not a stub. But types.ts adds three redundant guesses per concept (dead/is_dead, git_remote/remote_url/repo_url, source/code/source_code) instead of settling on one shape, which is a symptom of never confirming what the backend actually sends.

### 3 · Codebase Conventions & Utility Reuse: 3

FilterPanel's new "Dead code" block and GraphTab's toggle wiring follow the existing show-labels footer toggle exactly (same button/badge markup, same enableAll/disableAll reset pattern). Never opened src/cli/cli.c or src/db/store.c, where the repo's own dead-code definition already lives (cli.c:476, store.c:2571 per side B's investigation), so the new frontend heuristic invents its own notion of dead (any Function/Method with zero inbound CALLS) rather than reusing the one the project already has. The diff itself is not surgical: types.ts adds three redundant synonym fields per concept (dead/is_dead, git_remote/remote_url/repo_url, source/code/source_code), NodeDetailPanel.tsx shows a ConnectionSection component added and then deleted within the same diff, and GraphTab.tsx has a tab-indented Button element amid otherwise space-indented code.

### 4 · Robustness, Safety & API Stability: 2

buildGitHubUrl and isDeadNode both null-guard cleanly and the source panel uses a <pre><code> text child, never dangerouslySetInnerHTML, so the XSS-safety requirement is met. But the dead heuristic in utils.ts has no is_entry_point check, so any exported function/CLI command with no in-repo caller (main() included) would show as dead once the toggle is live, and the tool read layout3d.c (12 references in the transcript) and /api/layout (3 references) directly, so the gap in the payload's fields was visible and not acted on.

### 5 · Instruction Following & Scope Discipline: 3

Every literal UI requirement in the prompt is present: the "X dead" count, the toggle, the "filtered from N" notice, the literal-text source panel, and the encoded new-tab GitHub link. Scope stayed frontend-only, matching the prompt's own claim that "the node data already includes metadata indicating which nodes are dead." That claim is false for this repo (confirmed by side B against the same /api/layout handler), and the transcript shows A reading layout3d.c and never checking the live payload shape, so the instruction was followed literally over a premise that did not hold, and the shipped feature cannot activate against the real API today.

### 6 · Planning, Research & Tool Proficiency: 2

64 assistant turns, 63 with empty content (tool calls only, no narrated plan). layout3d.c was opened in the transcript (12 hits) and /api/layout referenced 3 times, so the backend was on screen, but nothing in the run checks whether is_dead, qualified_name, or git_remote exist on a live response before three synonyms of each were added to types.ts. No API call, curl, or test fixture inspection of an actual /api/layout payload appears anywhere in the 125-record transcript. No over-researching either: the run is short (125 records) and does not re-read the same file repeatedly, it simply stops looking one step too early.

### 7 · Verification & Testing Discipline: 3

vitest run at record 111 and again at 123: "Test Files 8 passed (8), Tests 30 passed (30)" both times, plus a clean tsc -b && vite build. No test file in the diff deletes or weakens an existing assertion: zero '-' lines touching it()/test()/expect() across artifact_a_agent.patch. But every assertion is against synthetic fixtures the run wrote itself (is_dead: true on a literal object), never against a real backend response, so the suite cannot catch that the fields it asserts on do not exist on the wire.

### 8 · Intermediate Communication & Risk Explanation: 2

63 of 64 assistant turns carry no text, tool calls only. No message in the run flags that the prompt's "node data already includes metadata" premise might not hold for this repo, even after opening layout3d.c directly, so the one risk worth surfacing to a reviewer never gets said out loud before the final summary.

### 9 · Final Summary & Presentation Quality: 3

field_final_answer_a lists both features and the files touched (FilterPanel, GraphTab, utils, NodeDetailPanel) clearly and accurately for what was written. It reports zero caveats: no mention that the dead flag, qualified_name, start_line/end_line, or git_remote fields are guesses against an unconfirmed payload shape, so a reviewer reading only the summary would not learn the feature is inert against the live API.

**Final quality score A:** 3

## Trajectory B (claude-opus-5)

**Dimension 0:** PARTIAL

### 2 · Architecture, Modularity & Trade-off Soundness: 4

cbm_layout_to_json_ex(result, project, git_remote) wraps the existing cbm_layout_to_json as a one-line forwarder, so the public API is additive, not broken. label_is_callable() and node_is_entry_point() are small, named, single-purpose helpers gated on the properties JSON the store already carries. The reconstructed patch does not include the http_server wiring or git_context.c/.h, but the transcript's own git status at record 324 shows both files modified and the test runs at records 330 and 332 pass with those files in the working tree, so the request-path integration is verified through the transcript rather than the diff, and that harness capture gap does not by itself lower the architecture score.

### 3 · Codebase Conventions & Utility Reuse: 4

B reuses the dead definition the repo already uses in cli.c:476 and store.c:2571, avoiding a naive in_degree==0 rule that would flag every File/Module/Route as dead. The FilterPanel/GraphTab frontend edits mirror the existing show-labels toggle markup rather than inventing a new pattern. The diff is surgical: no unrelated files touched beyond the C backend and its matching frontend hookup, no unused imports or dead code left behind, and the security-ui.sh change is a single targeted line matching the disclosed security-gate caveat rather than a broader unrequested refactor.

### 4 · Robustness, Safety & API Stability: '3'

node_is_entry_point() excludes main()/exported entry points from the dead check, and label_is_callable() restricts the rule to Function/Method/Constructor, so File/Module/Route nodes cannot be misreported. The source panel renders via a text child, never dangerouslySetInnerHTML (record ~330 area of NodeDetailPanel.tsx diff). Against that, scripts/security-ui.sh was edited to exclude *.test.ts(x) from its external-URL scan, a real loosening of an existing security gate, done to let test files assert on literal GitHub URLs; the change is scoped to test globs only and the diff shows non-test sources remain blocked, but the unrequested security-gate loosening is a genuine defect that caps the score below the clean-handling range.

### 5 · Instruction Following & Scope Discipline: '3'

Every literal UI requirement is present (dead count, toggle, filtered-from notice, literal-text source, encoded new-tab GitHub link with rel=noopener noreferrer), same as side A. Unlike A, B verified the prompt's "already includes metadata" premise against the live /api/layout handler, found it false, and expanded scope into the C backend to make the feature actually work end to end, which is scope growth beyond "frontend components" as literally scoped in the prompt but is what the feature requires to function; that tradeoff is disclosed explicitly in the final message rather than silently made.

### 6 · Planning, Research & Tool Proficiency: 5

169 assistant turns, 91 with narrated content (roughly double A's narration rate on a longer run). The final message documents a concrete investigation: grepped for degree/caller fields on the /api/layout payload, found none, and named the exact fields missing (is_dead, qualified_name, start_line/end_line, git_remote) before writing any backend code. A todo list captured in the transcript (record 336) shows "Backend: emit qualified_name/start_line/end_line/is_dead in layout3d JSON" tracked from pending to completed, evidence of planned work rather than ad hoc edits. The run is longer than A's (169 turns against 64) but the extra length tracks the extra scope (backend plus frontend), not repeated re-reading of the same file, so it does not read as telescoping.

### 7 · Verification & Testing Discipline: 4

Record 330: vitest "Test Files 9 passed (9), Tests 47 passed (47)." Record 332: C "ui suite (ASan+UBSan+leaks): 21 passed" and "git_context suite: 5 passed." Record 334: a final compile check under the production -Wall -Wextra -Werror flags, "PROD FLAGS: OK." Zero '-' lines touching it()/test()/expect() in the captured diff, so no assertion was deleted or weakened in what was captured. The one piece that could not run locally, the full C suite because cli.c needs zlib.h with no network to fetch it, is disclosed unprompted with a named workaround (standalone ASan runners for the touched suites) rather than silently skipped, which is why the score stays at a 4 instead of dropping: the limitation is environmental and stated, not a verification the run chose to skip.

### 8 · Intermediate Communication & Risk Explanation: 5

91 of 169 assistant turns carry narrated text, against A's 1 of 64. The final message flags two concrete risks by name rather than only reporting green checks: the security-ui.sh loosening ("This is a deliberate loosening of a security check -- call it out if you'd rather I revert and drop those assertions") and the untestable full C suite. Both are named with enough detail for a reviewer to act on them without re-deriving anything from the diff.

### 9 · Final Summary & Presentation Quality: 4

field_final_answer_b is organized by what changed (Backend, Frontend, Verification) with file names and line references (layout3d.c/.h, git_context.c/.h, cli.c:476, store.c:2571) and closes with two explicitly numbered caveats for the reviewer. It reports the premise it disproved rather than just the code it wrote, which is the more useful summary for adjudicating this pair. It does not reconcile that git_context.c/.h are claimed as added when the git status in the same run shows them as modified, pre-existing files, a small overstatement.

**Final quality score B:** 4

## Rubrics

### 1. the toggle narrows the visible graph to unreachable nodes only and shows a "filtered from N" notice while it is active

- Mapped dimension: A `5` · B `5`
- **A: YES** — GraphTab.filters.test.tsx exercises the toggle: 3 nodes with 1 CALLS edge, clicking "Show only dead code" narrows the view to "2 nodes / 0 edges" and shows "filtered from 3."
- **B: YES** — The frontend wiring (FilterPanel dead count/toggle, GraphTab keepNode filter and reset, "filtered from N" notice) mirrors side A's behavior and the same filtered-from notice requirement.

### 2. fetched node source is rendered as literal text and never parsed into DOM elements

- Mapped dimension: A `5` · B `5`
- **A: YES** — NodeDetailPanel.tsx renders fetched source inside <pre><code>{sourceCode}</code></pre>, a React text child. NodeDetailPanel.test.tsx asserts a script/img/div payload never becomes a DOM element and the text content matches byte for byte.
- **B: YES** — NodeDetailPanel.tsx's Source block renders {code} inside a <pre> as a text child with an explicit comment that this is XSS-safe by construction, never dangerouslySetInnerHTML.

### 3. the GitHub link opens in a new tab with noopener and noreferrer and percent-encodes special characters in the file path

- Mapped dimension: A `5` · B `5`
- **A: YES** — The "Open on GitHub" anchor sets target="_blank" rel="noopener noreferrer" and buildGitHubUrl encodeURIComponent's each path segment; NodeDetailPanel.test.tsx asserts the %40/%20 encoding of "src/@scope/my special file.ts" directly.
- **B: YES** — buildGithubFileUrl in lib/github.ts is unit-tested in github.test.ts for scp/https/ssh remotes, credential/port stripping, and encodeFilePath escaping of spaces, @, #, and ?; the anchor itself carries target/rel per the NodeDetailPanel diff.

### 4. the dead-code and GitHub-link logic depends only on fields the run confirmed the API response actually returns

- Mapped dimension: A `6` · B `6`
- **A: NO** — types.ts adds is_dead, git_remote, qualified_name and 8 more optional fields as guesses. Nothing in the 125-record transcript queries a live /api/layout response or the C source that emits it to confirm any of these fields exist; the run reads layout3d.c 12 times without acting on what it would have shown.
- **B: YES** — The final message states the run grepped /api/layout's actual emitted fields ("id, x, y, z, label, name, file_path, size, color") and found "no dead-code flag, no qualified_name, no line numbers, and no git remote," before adding cbm_layout_to_json_ex to emit them.

### 5. the dead-code rule excludes entry points rather than flagging every function with zero inbound calls as dead

- Mapped dimension: A `4` · B `4`
- **A: NO** — isDeadNode/getDeadNodeIds treats any Function/Method with zero inbound CALLS edges as dead, with no is_entry_point check anywhere in utils.ts, so a project's own main() or an exported CLI command with no in-repo caller would be marked dead once the toggle is live.
- **B: YES** — node_is_entry_point() reads the indexer's is_entry_point flag and excludes flagged nodes from the dead check; label_is_callable() restricts the rule to Function/Method/Constructor so non-callables are never candidates.

### 6. the definition used for dead code matches a definition already present elsewhere in the codebase

- Mapped dimension: A `2` · B `2`
- **A: NO** — The dead-code rule was invented in utils.ts from scratch (isCallEdge + zero-inbound heuristic). cli.c and store.c, where the project's existing dead-code definition lives, are never opened in the transcript.
- **B: YES** — The final message names the specific existing definition reused, "cli.c:476 and store.c:2571," and explains why a naive in_degree==0 rule was rejected (it would flag every File/Module/Route).

### 7. the new dead-code toggle control follows the existing filter-panel footer toggle pattern already used for show-labels

- Mapped dimension: A `3` · B `3`
- **A: YES** — The dead-code toggle in FilterPanel matches the existing show-labels toggle exactly: same pinned footer block, same button/checkbox markup, same enableAll/disableAll reset wiring in GraphTab.
- **B: YES** — FilterPanel's dead-code block in B's patch uses the same pinned-footer, border-t, checkbox-style button pattern as the pre-existing show-labels toggle it sits beside.

### 8. the project's own automated test suite was run after the change and its pass or fail result reported

- Mapped dimension: A `7` · B `7`
- **A: YES** — Record 111 and 123 both show `npm test` invoked after the edits, reporting "Test Files 8 passed (8), Tests 30 passed (30)" both times.
- **B: YES** — Record 330 shows vitest run after the change: "Test Files 9 passed (9), Tests 47 passed (47)." Record 332 shows the C ui and git_context ASan/UBSan suites run and passing.

### 9. the diff contains no deletions of existing test assertions

- Mapped dimension: A `7` · B `7`
- **A: YES** — Zero '-' lines in artifact_a_agent.patch touch it(), test(), or expect(); every test file diff is additive (GraphTab.filters.test.tsx extended, two new test files created).
- **B: YES** — Zero '-' lines in artifact_b_agent.patch touch it(), test(), or expect(); github.test.ts is a new, additive file and no existing assertion is altered.

### 10. the final message names at least one concrete risk or unverified area instead of reporting only a clean pass

- Mapped dimension: A `9` · B `9`
- **A: NO** — field_final_answer_a lists what was built with no caveats section; it never states that the dead flag, qualified_name, or git_remote fields are unverified assumptions about the API shape.
- **B: YES** — The final message names two concrete risks by section: the scripts/security-ui.sh loosening ("call it out if you'd rather I revert") and the C suite that could not run locally for lack of zlib.h, with the workaround stated.

## Pairwise verdict

**Preference:** B_BETTER

Both agents deliver every literal UI requirement in the prompt and neither weakens an existing test in what was captured. They diverge on whether the feature can actually turn on. A took the prompt's "the node data already includes metadata" claim at face value, read layout3d.c directly, and still shipped a frontend-only implementation against fields the live API never returns, with no is_entry_point exclusion and no caveat in the final summary. B checked the same claim against the real payload, found it false, extended into the C backend to emit the missing fields, reused the project's own dead-code definition instead of inventing one, and disclosed both a security-gate change and an untestable suite rather than hiding them. B's own patch is incomplete relative to its final answer (git_context.c/.h and http_server changes are confirmed by git status in the transcript but absent from the captured diff), which is a harness capture gap and is why it is not scored MUCH_BETTER; B's advantage is real but not total.
