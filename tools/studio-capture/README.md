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
- **Fallback:** record a DevTools HAR as described in docs/09-studio-flow.md §2.3.

## How it was tested

`capture.js` was run in a simulated page whose API replays the responses recorded
in a real Studio HAR (2026-09-15). Checked:

- all requests carried the page's token, and neither the token nor any S3
  signature appeared in the output;
- `studio.py har` on the output reproduced the task folder **byte for byte**, the
  same as extracting the DevTools HAR.

It hasn't yet run against live Studio. Confirm on the first real capture.
