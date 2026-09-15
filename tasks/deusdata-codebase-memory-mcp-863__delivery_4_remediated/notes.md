# deusdata-codebase-memory-mcp-863__delivery_4_remediated: working notes

Claimed 2026-09-15 by the user. Follows [docs/09-studio-flow.md](../../docs/09-studio-flow.md).

## Task facts

- `feature_implementation`, JavaScript/TypeScript, hard (Opus 4.8 pass@8 = 0/8 per
  `task.toml`), format `SWE_BENCH`.
- Repo https://github.com/DeusData/codebase-memory-mcp at base commit
  `9987a4eae00a7ea2beda3f56ce3fa386f2fda085` (`environment/Dockerfile`).
- Harness `opencode`. **A = gemini-3.7-flash** (Gemini side), **B = claude-opus-5**.
- **Patches:** both are reconstructed from edit calls; B's also leaves out one
  shell-command edit.
- **Rubrics:** 10 criteria.
- **Grader:** `tests/grade.py` gives reward 1 only when **every** FAIL_TO_PASS test
  is individually observed passing. There are no partial credits.
- **History:** Seed → Claimable (9/5–9/6) → Annotating and Final QC by the first
  annotator (9/9) → In Review, then returned by the reviewer (9/15 04:58 UTC) →
  Claimable → Annotating (user, 9/15 16:52 UTC).

## Why it was returned (from the HAR)

**Reviewer inline comment (9/15 04:58 UTC):** *"Both Model A and Model B must have a
rubric pass rate strictly below 75%. Please review the rubric assessments and
revise where supported by the evidence, keeping all judgments accurate."*
Currently A is 6/10 and **B is 10/10**.

**Latest AutoQC** (9/15 05:17 UTC, spec v10, task version 7): **13/14 pass**. The
one failure is `aq_a1` **rubric atomicity**:

| Rubric | Problem | AutoQC's suggested split |
|---|---|---|
| 3 | new tab + rel attributes **and** percent-encoding | (a) opens in a new tab with `rel="noopener noreferrer"`; (b) percent-encodes special characters in the file path |
| 4 | dead-code logic **and** GitHub-link logic | one rubric per logic area |
| 1 | filter behaviour **and** "filtered from N" notice | (a) the toggle narrows to unreachable nodes; (b) the notice shows the original count while active |

Details are in `studio/autoqc.md`.

## Fetch status

- [x] HAR 1 (2026-09-15): task, rubrics, 9/10 bundle files, A's transcript, reviewer
      comment, history, AutoQC, QC specs
- [x] HAR 2 (2026-09-15, 225 MB): adds **B's transcript and logs**. Readable versions
      are `trajectories/A.md` and `B.md`, where "record N" = `## [N]`.
- [ ] `harbor/environment/prompt_statement.md`: still not clicked (low priority)
- [ ] Real agent patches (only the reconstructed ones so far)

## ⚠ Dimension 0: the hidden tests require things the prompt never states

Read from `tests/config.json`, `tests/test.patch` and `solution/golden.patch`.
**Nothing has been run.**

The three FAIL_TO_PASS tests are all in files that `test.patch` adds:

1. **`GraphTab.deadcode.test.tsx` · "shows the dead count and filters to only dead
   code on toggle"**
   - The fixture marks nodes with **`status: "dead"` / `status: "normal"`** and
     `in_calls`.
   - It expects `"1 dead"`, then `/filtered from 2/` after toggling.
   - The prompt only says *"The node data already includes metadata indicating
     which nodes are dead"*. It never names the `status` field or its values.
   - The golden patch introduces `status` (`NodeStatus` in `types.ts`,
     `n.status !== "dead"` in GraphTab) **and emits it from the C backend**
     (`layout3d.c`, and `tests/test_ui.c` asserts `"status":"dead"`). So at the
     base commit the metadata the prompt describes doesn't exist. That is the
     premise B reported as false.
2. **`NodeDetailPanel.test.tsx` · "renders fetched source as escaped text"**
   - It renders `<NodeDetailPanel … project="demo" repoInfo={REPO} />` and finds
     the source with `selector: "pre"`.
3. **`NodeDetailPanel.test.tsx` · "builds an https GitHub deep-link with
   URL-encoded path segments"**
   - It passes a **`repoInfo: RepoInfo`** prop (`root_path`, `branch`,
     `remote_url`, `web_base`, `blob_base`).
   - It expects `href` to start with `…/blob/main/`, to contain
     `src/weird%20name/%40mod.ts` and `#L10-L20`, and the rel/target attributes.
   - The prompt says only *"when the repository's remote URL is known"*. It never
     names the `repoInfo` prop, the `RepoInfo` shape or the branch.

**What that likely means for each side** (reading the patches only, not run):

- **A:**
  - Its dead rule uses `is_dead`/`dead`, falling back to CALLS edges. On this
    fixture the edge fallback counts node 2 as dead, which is **"1 dead" for the
    wrong node**. Test 1 could pass by accident.
  - It renders `<pre><code>{source}</code></pre>`. Testing Library's `selector:
    "pre"` text match only reads a `<pre>`'s direct text, so test 2 likely fails.
  - It takes a `gitRemote` prop, not `repoInfo`, so the link never renders and
    test 3 fails.
- **B:**
  - It filters on `n.is_dead === true`, so this fixture gives "0 dead" and test 1
    fails.
  - It renders `<pre>{code}</pre>`, so test 2 may pass if the button renders. The
    button markup is in the missing shell edit.
  - It takes a `gitRemote` prop and uses `blob/HEAD/`, so test 3 fails.

Neither side can reach reward 1. That is consistent with the recorded 0.0 / 0.0 and
the automated `REJECT_BOTH_FAIL`.

**The failures come from the task, not the agents.** Two of the three tests pin an
interface the prompt doesn't state (`status: "dead"`, the `repoInfo` prop and the
`main` branch), and the first depends on backend data that doesn't exist at the
base commit. That is the "a test that picks one valid implementation is a hidden
requirement" defect (CLAUDE.md; `03` §2).

**Recommendation:** don't remediate the rubrics yet.

1. Post the evidence above in `#anton-general-bf1` and ask whether to **Flag
   Defective Task** or to annotate anyway (reporting Dimension 0 as FAIL / FAIL,
   which the Task Auditor checklist rejects as an ineligible pair).
2. If they say annotate anyway:
   - Dimension 0 for both sides becomes FAIL, each with a reason citing the test
     ids above;
   - then do the rubric work below.

## If told to annotate: the existing annotation's problems

1. B's dim 4 and dim 5 have been stored as `"3"` since version 3. They show as
   *required* in Navigation; re-select them. The earlier AutoQC run passed its
   schema check anyway.
2. Rubrics 1, 3 and 4 need splitting (AutoQC). Splitting gives 13 rubrics; then
   each side's YES rate must be below 75% (≤9 of 13).
3. B's YES rate must fall with **honest** answers. Candidates, all to verify in
   transcript B:
   - "Existing security or CI check scripts are left unmodified" (environment:
     `scripts/security-ui.sh`; Dim 4). B edited it per `patch_b.diff`, so NO.
   - "The GitHub link uses the repository's configured branch rather than a fixed
     ref" (Dim 4). B uses `HEAD`; A defaults to `main`. Needs thought.
   - ~~"A test exercises the dead-code toggle…"~~ **Dropped after transcript
     check.** B tested it too (B[208] test DOM shows "filtered from 2"; B[220]
     shows 11 tests in B's NodeDetailPanel.test.tsx).
4. A is scored using B's findings (dim 3 "per side B's investigation", dim 5
   "confirmed by side B"). Rewrite each side on its own evidence.
5. B's rubric reasons 4, 6 and 10 cite B's final message, not tool output.
   B's rubric 1 reason gives no B-specific evidence.
6. A's dim 3 "ConnectionSection added and then deleted": **confirmed as a process
   slip, not a diff defect.** A's build failed at A[95] ("symbol ConnectionSection
   has already been declared") and A fixed it, so the final code is clean. Move it
   to Dim 6, and credit A's build check under Dim 7.
8. B's dim 8 reason says "91 of 169 turns carry narrated text". It's the reverse:
   78 with text, 91 silent. Fix the number.
9. B's "reuses `cli.c:476` / `store.c:2571`" is only in B's final message; the
   transcript never shows those lines. Don't cite it as verified.
7. The premise that `/api/layout` sends no dead-code flag is now **confirmed by the
   task itself**: the golden patch adds `status` in `layout3d.c`. Cite that, not
   B's message.

## Transcript verification (HAR 2, 2026-09-15)

"Record N" in the existing annotation = message index N in
`trajectory_messages`. Checked: B[324] git status, B[330] 47 tests, B[332] ASan
suites, B[334] PROD FLAGS, B[336] todo list, A[111] and A[123] 30 tests. All match.

**Limitation:** every tool call was imported with arguments `{}`. Results are
recorded, but the commands aren't, so no reason can cite the exact command an agent
typed.

| Claim in the existing annotation | Verdict | Evidence |
|---|---|---|
| A: 63 of 64 assistant turns silent | ✅ true | only A[124] (final answer) has text |
| B: "91 of 169 turns carry narrated text" | ❌ **inverted** | 78 with text, 91 silent (AutoQC also flagged the count) |
| A read `layout3d.c` "12 hits" / `/api/layout` "3 references" | ⚠ count wrong, substance true | A read `src/ui/layout3d.c` at A[33], A[35], A[37] and the `GET /api/layout` handler at A[39]; it still assumed `is_dead` etc. |
| A never opened `cli.c` / `store.c` | ✅ essentially true | only grep hits A[55], A[67]; no read of the dead-code definition |
| A has no `is_entry_point` check | ✅ true | no mention anywhere in A |
| A dim 3: "ConnectionSection added then deleted within the same diff" | ❌ **wrong dimension** | A duplicated it by mistake, the build failed at A[95] ("symbol ConnectionSection has already been declared"), and A fixed it. The final code has no duplicate, so it's not a Dim 3 diff defect. It's a Dim 6 process slip, caught by A's own build (a Dim 7 positive) |
| B: `/api/layout` carries no dead flag (premise false) | ✅ true | B[2] exploration report: "no degree, no in/out counts, no `is_dead`, no `callers`". Also confirmed by the golden patch adding `status` in `layout3d.c` |
| B reuses the definition at `cli.c:476` / `store.c:2571` | ⚠ unverified | those line refs appear only in B's final message B[337]; the transcript shows `cli.c:459` (B[10]) |
| B: zlib missing, could not run the full C suite | ✅ true | B[138] `zlib.h: No such file`, B[142] package unavailable, B[143] |
| B mutation-tested the security assertions | ✅ true | B[221] "The mutation is caught", B[225] `encodeURI` mutation caught |
| B relaxed `scripts/security-ui.sh` | ✅ true | B[316] reads it, B[324] git status ` M scripts/security-ui.sh`, B[332] "UI security audit passed" afterwards |
| B: 47 vitest, ASan suites, prod flags | ✅ true | B[330], B[332], B[334] |

### Dimension 0: reading the hidden tests against the final code (not run)

- **Test 1** (`status: "dead"` fixture; edge 2→1 CALLS):
  - **A:** its edge fallback marks node **2** as dead. The count reads "1 dead" and
    the toggle leaves one node, so the existing HUD's "filtered from 2" appears
    (B[101] confirms the HUD already renders it). **Could pass by accident, for the
    wrong node.**
  - **B:** it filters on `is_dead === true`, so "0 dead". **Fails.**
- **Test 2** (`findByText(fn, { selector: "pre" })`):
  - **A:** renders `<pre><code>{source}</code></pre>`. Testing Library matches a
    `<pre>` only on its own text children, so **likely fails.**
  - **B:** renders `<pre>{code}</pre>`. **Likely passes** if its button renders
    with `project` + `qualified_name`.
- **Test 3** (`repoInfo` prop, `blob/main/`): **both fail.** Neither accepts
  `repoInfo`; B also uses `blob/HEAD`.
- **Also:** A and B each created their own `NodeDetailPanel.test.tsx`, and
  `test.patch` adds a file at the same path, so the test patch may not apply
  cleanly.

At most 1 of 3 each, and the grader needs all 3, so reward 0 / 0 matches. The
blocking tests pin an interface the prompt never states (`status`, `repoInfo`,
`main`). **The defective-task finding stands.**
