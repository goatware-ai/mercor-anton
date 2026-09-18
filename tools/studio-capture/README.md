# Anton Studio Capture (Chrome extension)

One click on a Studio task page downloads everything the review needs: the task and
rubrics, both transcripts and logs, every bundle file, reviewer comments, history,
AutoQC audits and QC specs, the annotation form definition, and each rollout's real
`agent.patch` — which the page itself never downloads, so no DevTools HAR has it. The download is a single `.har` file that
`tasks/studio.py har` unpacks into `tasks/<task-id>/`. It replaces recording a
DevTools HAR by hand (docs/09-studio-flow.md §2).

Local extensions were confirmed OK by the Anton tooling channel (2026-09-15).

## What it does and doesn't do

- It runs only on `https://studio.mercor.com/*`. It requests **no browser
  permissions**.
- It makes the same API requests the task page makes when you click through its
  tabs, using the page's own login headers from its most recent request. The
  headers stay in memory and are **never written to the file**.
- Signed S3 download URLs are stripped before saving.
- It sends nothing anywhere. The only output is the file in your Downloads.

## Install (once)

Chrome loads unpacked extensions more reliably from a Windows folder than from the
WSL path, so copy it out first:

```bash
rm -rf /mnt/c/Users/klayt/anton-studio-capture
cp -r /home/klayt/projects/mercor-anton/tools/studio-capture /mnt/c/Users/klayt/anton-studio-capture
```

1. Open `chrome://extensions`.
2. Turn on **Developer mode** (top right).
3. Click **Load unpacked** and pick `C:\Users\klayt\anton-studio-capture`.
4. Reload any open Studio tab.

**After an update:** run the copy command again, then click ↻ on the extension card
in `chrome://extensions` and reload the Studio tab.

## Use (every task)

1. Open the task page in Studio and wait for it to finish loading.
2. Click **⬇ Capture task for review**, bottom-left of the page.
3. When it says **✅ Saved**, the file is in Downloads as
   `studio-capture_<task name>_<time>.har`.
4. Run, or ask Claude to run:

   ```bash
   python3 tasks/studio.py har "/mnt/c/Users/klayt/Downloads/studio-capture_<…>.har"
   python3 tasks/studio.py check tasks/<task-id>
   ```

## Capture the board

On a Studio page that lists tasks, the same button reads
**⬇ Capture board (N tasks seen)**. It replaces the CSV export in
docs/08-task-board.md §4.

1. Open the task list, set the filter you want (for example Status = Claimable)
   and wait for it to load. The button shows **N of T tasks**, where T is the
   total Studio reports for that filter. If N is below T, open the other pages of
   the list until they match.
2. Click the button. When it says **✅ Saved**, the file is in Downloads as
   `studio-board_<time>.har`.
3. Run, or ask Claude to run:

   ```bash
   python3 tasks/studio.py board "/mnt/c/Users/klayt/Downloads/studio-board_<…>.har"
   ```

   It writes `notes/board-<date>.md`, one row per task: status, owner, type,
   harness, models, Dimension 0, preference, final scores, rubric YES rates and
   review cycles. It creates no task folders.

The extension never requests the list itself. It reads task ids from the list
responses the page receives (`GET /tasks/world/{world_id}/detailed`), then fetches
each task with `GET /tasks/{id}`, the request a task page makes. If it saw no list
response it falls back to the task links drawn on the page. The file also keeps
the page's list responses. Each task's `task_schema` is left out of the file; a
task capture has it.

Only the list on screen counts. Pages of one filter add up; a new filter or sort
replaces the ids held. Version 1.1.0 added every list together: on 2026-09-18 the
page loaded the unfiltered list (100 tasks) and then the Claimable filter (52), and
the capture fetched 150. `board` handles such a file by keeping the last list.

A board file holds other annotators' labels. The independence note at the top of
docs/08-task-board.md applies to it.

Capture again after every **Save Changes** or AutoQC run to see what Studio stored.
Delete old capture files from Downloads when the task is done; they hold task
content.

## If it fails

- **"Could not load the task"** or 401 errors: the page hadn't made an
  authenticated request yet, or the login expired. Reload the page (F5), wait, then
  click again.
- **"Saved with N error(s)":** the button lists the failing requests, and `har`
  prints them as `! capture error`. One missing bundle file isn't fatal; tell
  Claude which ones failed.
- **No button:** check the extension is enabled, the URL looks like
  `/annotator/tasks/task_…`, and the tab was reloaded after installing.
- **No board button on a list page:** the button appears only after a task id has
  been seen. Reload the page (F5) so the extension sees the list load. If it still
  doesn't appear, the list response has no `"task_id"` keys and the rows aren't
  links; record a DevTools HAR of the list page and give it to Claude.
- **Fallback:** record a DevTools HAR as described in docs/09-studio-flow.md §2.3.

## How it was tested

`capture.js` was run in a simulated page whose API replays the responses recorded
in a real Studio HAR (2026-09-15). Checked:

- all requests carried the page's token, and neither the token nor any S3
  signature appeared in the output;
- `studio.py har` on the output reproduced the task folder **byte for byte**, the
  same as extracting the DevTools HAR.

The first live task capture was 2026-09-15 (29 entries, no errors).

The board capture (1.1.0, 2026-09-18) was run in a simulated list page: a list
response naming three tasks, a fourth task present only as a link, and one task
returning 500. Checked:

- the button counted 4 tasks, saved 3, and reported `500 /tasks/task_ccc…`;
- the page still read its own list response;
- neither the token nor `task_schema` appeared in the file;
- `studio.py har` on a board file ran `board` and created no task folder;
- task capture output was identical to 1.0.0 on the same replay.

The first live board capture (1.1.0, 2026-09-18) fetched 150 tasks with no errors
but should have fetched 52; see above. 1.1.1 was checked by replaying that file's
two real list responses, in order and with the unfiltered one arriving last: both
runs showed **52 of 52 tasks**, made 52 task requests and saved one list entry.
1.1.1 hasn't yet run against live Studio.
