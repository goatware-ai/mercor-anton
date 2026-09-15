/* Anton Studio Capture
 *
 * Adds a "Capture task" button to Studio task pages (/annotator/tasks/task_…).
 * Clicking it requests every piece of the task from Studio's own API, the same
 * requests the page makes when you click through its tabs, and downloads one
 * HAR-shaped file that `python3 tasks/studio.py har <file>` unpacks.
 *
 * Credentials: the script runs in the page and reuses the headers of the page's
 * own most recent API request (authorization, x-account-id, x-campaign-id,
 * x-company-id). They live only in memory and are never written to the file.
 * Signed S3 URLs are also stripped before saving. Endpoints are documented in
 * docs/09-studio-flow.md §1.
 */
(() => {
  const API = "https://api.studio.mercor.com";
  const KEEP_HEADERS = ["authorization", "x-account-id", "x-campaign-id", "x-company-id"];
  const TASK_PATH = /^\/annotator\/tasks\/(task_[0-9a-f]{32})/;
  const originalFetch = window.fetch.bind(window);

  /* ── Remember the page's own API headers ─────────────────────────────── */
  let pageInit = null; // { headers: Headers, credentials }

  window.fetch = function (input, init) {
    try {
      const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      if (url && new URL(url, location.href).origin === API) {
        const headers = new Headers(input instanceof Request ? input.headers : undefined);
        if (init && init.headers) new Headers(init.headers).forEach((v, k) => headers.set(k, v));
        if (KEEP_HEADERS.some((k) => headers.has(k))) {
          pageInit = {
            headers,
            credentials: (init && init.credentials) || (input instanceof Request ? input.credentials : "include"),
          };
        }
      }
    } catch (_) {
      /* never interfere with the page's own request */
    }
    return originalFetch(input, init);
  };

  function apiHeaders(tokenOverride) {
    const h = new Headers({ accept: "application/json" });
    if (pageInit) for (const k of KEEP_HEADERS) if (pageInit.headers.has(k)) h.set(k, pageInit.headers.get(k));
    if (tokenOverride) h.set("authorization", `Bearer ${tokenOverride}`);
    return h;
  }

  /* ── Capture ─────────────────────────────────────────────────────────── */
  function toBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    for (let i = 0; i < bytes.length; i += 0x8000) {
      binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    }
    return btoa(binary);
  }

  async function captureTask(taskId, progress) {
    const entries = [];
    const errors = [];
    const record = (url, status, mimeType, text, encoding) =>
      entries.push({
        request: { method: "GET", url, headers: [] },
        response: { status, headers: [], content: { mimeType, text, ...(encoding ? { encoding } : {}) } },
      });

    async function api(path, { save = true, optional = false } = {}) {
      const url = API + path;
      let res = await originalFetch(url, { headers: apiHeaders(), credentials: pageInit?.credentials || "include" });
      if (res.status === 401 && window.Clerk?.session?.getToken) {
        const token = await window.Clerk.session.getToken().catch(() => null);
        if (token) res = await originalFetch(url, { headers: apiHeaders(token), credentials: "include" });
      }
      const text = await res.text();
      if (!res.ok) {
        if (!optional) errors.push(`${res.status} ${path}`);
        return null;
      }
      if (save) record(url, res.status, res.headers.get("content-type") || "application/json", text);
      try {
        return JSON.parse(text);
      } catch (_) {
        return null;
      }
    }

    /* A snapshot file: ask for a signed URL (never saved), then save the bytes. */
    async function fetchSnapshotFile(urlPath, rel) {
      const signed = await api(`${urlPath}?file_path=${encodeURIComponent(rel)}`, { save: false, optional: true });
      if (!signed?.url) {
        errors.push(`no download url for ${rel}`);
        return;
      }
      const res = await originalFetch(signed.url);
      if (!res.ok) {
        errors.push(`${res.status} ${rel}`);
        return;
      }
      const u = new URL(signed.url);
      record(u.origin + u.pathname, res.status, res.headers.get("content-type") || "application/octet-stream",
             toBase64(await res.arrayBuffer()), "base64");
    }

    progress("task");
    const task = await api(`/tasks/${taskId}`);
    if (!task) throw new Error("Could not load the task. Reload the page (F5), wait for it to finish, then click Capture again.");
    const cf = task.custom_fields || {};

    progress("rubrics, history, comments, form");
    await Promise.all([
      api(`/verifiers/task/${taskId}`),
      api(`/tasks/${taskId}/history`),
      api(`/inline-review-comments/task/${taskId}`),
      task.world_id ? api(`/worlds/${task.world_id}`) : null, // the annotation form definition
      task.world_id ? api(`/verifiers/world/${task.world_id}`, { optional: true }) : null,
    ]);

    progress("trajectories");
    const trajIds = new Set();
    try {
      const ledger = JSON.parse(cf.field_dl_run_ledger || "{}");
      for (const side of ["A", "B"]) if (ledger[side]?.trajectory_id) trajIds.add(ledger[side].trajectory_id);
    } catch (_) {}
    const listed = await api(`/trajectories/task/${taskId}`);
    for (const t of listed?.trajectories || []) trajIds.add(t.trajectory_id);
    for (const id of trajIds) {
      progress(`trajectory ${id.slice(0, 13)}…`);
      await api(`/trajectories/${id}`);
      await api(`/trajectory-logs/list/${id}`);
      /* Artifacts (agent.patch): the real patch, which the page's diff view never
         downloads, so a DevTools HAR can't contain it. */
      const snap = await api(`/snapshots/trajectory/${id}`, { optional: true });
      for (const f of snap?.files || []) {
        const rel = f.key.slice(f.key.indexOf("filesystem/"));
        await fetchSnapshotFile(`/snapshots/trajectory/${id}/file-url`, rel);
      }
    }

    progress("bundle files");
    const listing = await api(`/snapshots/task/${taskId}/input-files`);
    const files = listing?.files || [];
    let done = 0;
    for (const f of files) {
      const rel = f.key.slice(f.key.indexOf("filesystem/"));
      progress(`bundle ${++done}/${files.length}`);
      await fetchSnapshotFile(`/snapshots/task/${taskId}/file-url`, rel);
    }

    progress("AutoQC");
    const campaignId = new URLSearchParams(location.search).get("campaignId") || pageInit?.headers.get("x-campaign-id");
    await api(`/qc-audits/?subject_kind=task&subject_id=${taskId}&status=completed&limit=500`);
    if (campaignId) await api(`/qc-specs/?scope_type=campaign&scope_id=${campaignId}&subject_kind=task`, { optional: true });
    if (task.world_id) await api(`/qc-specs/?scope_type=world&scope_id=${task.world_id}&subject_kind=task`, { optional: true });

    return {
      log: {
        version: "1.2",
        creator: { name: "anton-studio-capture", version: "1.0.0" },
        entries,
        _capture: {
          task_id: taskId,
          task_name: task.task_name,
          captured_at: new Date().toISOString(),
          trajectories: trajIds.size,
          bundle_files: files.length,
          errors,
        },
      },
    };
  }

  function download(har, taskName) {
    const slug = (taskName || har.log._capture.task_id).replace(/[^\w.-]+/g, "_").slice(0, 80);
    const stamp = new Date().toISOString().replace(/[:T]/g, "-").slice(0, 16);
    const blob = new Blob([JSON.stringify(har)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `studio-capture_${slug}_${stamp}.har`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      URL.revokeObjectURL(a.href);
      a.remove();
    }, 10000);
  }

  /* ── Button ──────────────────────────────────────────────────────────── */
  let button = null;
  let busy = false;

  function ensureButton() {
    const match = location.pathname.match(TASK_PATH);
    if (!match) {
      if (button) button.style.display = "none";
      return;
    }
    if (!button) {
      button = document.createElement("button");
      button.type = "button";
      Object.assign(button.style, {
        position: "fixed", left: "16px", bottom: "16px", zIndex: 2147483647,
        padding: "8px 12px", borderRadius: "8px", border: "1px solid #6d5dfc",
        background: "#1b1830", color: "#e9e6ff", font: "600 12px system-ui, sans-serif",
        cursor: "pointer", boxShadow: "0 2px 8px rgba(0,0,0,.4)", maxWidth: "420px", textAlign: "left",
      });
      button.addEventListener("click", onClick);
      document.body.appendChild(button);
    }
    button.style.display = "block";
    if (!busy) button.textContent = "⬇ Capture task for review";
  }

  async function onClick() {
    const match = location.pathname.match(TASK_PATH);
    if (!match || busy) return;
    busy = true;
    const label = (t) => (button.textContent = `⏳ Capturing: ${t}`);
    try {
      const har = await captureTask(match[1], label);
      download(har, har.log._capture.task_name);
      const c = har.log._capture;
      button.textContent = c.errors.length
        ? `⚠ Saved with ${c.errors.length} error(s): ${c.errors.slice(0, 3).join(", ")}`
        : `✅ Saved: ${c.trajectories} trajectories, ${c.bundle_files} bundle files`;
    } catch (e) {
      button.textContent = `❌ ${e.message}`;
    } finally {
      busy = false;
      setTimeout(ensureButton, 15000);
    }
  }

  const start = () => {
    ensureButton();
    setInterval(ensureButton, 1000); // Studio is a single-page app; follow route changes
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
