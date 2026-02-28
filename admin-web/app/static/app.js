const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
const toast = document.getElementById("toast");

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.hidden = false;
  toast.style.background = isError ? "rgba(111, 24, 13, 0.96)" : "rgba(37, 29, 22, 0.96)";
  window.clearTimeout(showToast._timer);
  showToast._timer = window.setTimeout(() => {
    toast.hidden = true;
  }, 3500);
}

async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.method && options.method !== "GET") {
    headers.set("X-CSRF-Token", csrfToken);
    if (!headers.has("Content-Type") && options.body) {
      headers.set("Content-Type", "application/json");
    }
  }

  const response = await fetch(path, {
    credentials: "same-origin",
    ...options,
    headers,
  });

  if (response.status === 401) {
    window.location.href = "/login";
    throw new Error("Authentication required");
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // Keep default detail.
    }
    throw new Error(detail);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) {
    node.textContent = value;
  }
}

function renderJobs(jobs) {
  const root = document.getElementById("jobs-list");
  if (!root) {
    return;
  }

  if (!jobs.length) {
    root.innerHTML = "<p class='muted'>Aucun job pour le moment.</p>";
    return;
  }

  root.innerHTML = jobs
    .map((job) => {
      const output = job.stderr_tail || job.stdout_tail || "Aucune sortie.";
      return `
        <article class="job-card">
          <div class="job-head">
            <strong>${job.action}</strong>
            <span class="badge ${job.status}">${job.status}</span>
          </div>
          <p class="muted">${job.started_at || "En attente"}</p>
          <pre class="job-output">${escapeHtml(output)}</pre>
        </article>
      `;
    })
    .join("");
}

function renderWhitelist(names) {
  const root = document.getElementById("whitelist-list");
  if (!root) {
    return;
  }

  if (!names.length) {
    root.innerHTML = "<p class='muted'>Whitelist vide.</p>";
    return;
  }

  root.innerHTML = names.map((name) => `<span class="chip">${escapeHtml(name)}</span>`).join("");
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function refreshStatus() {
  const payload = await apiFetch("/api/status");
  setText("status-container", payload.container_state);
  setText("status-health", payload.health);
  setText(
    "status-players",
    payload.players_online === null ? "inconnu" : `${payload.players_online}/${payload.players_max ?? "?"}`
  );
  setText("status-whitelist", String(payload.whitelist_count));
  setText("status-updated", `Mise a jour: ${payload.updated_at}`);
  setText("status-line", payload.last_status_line || "Aucune ligne de statut.");
}

async function refreshLogs() {
  const payload = await apiFetch("/api/logs?tail=200");
  setText("logs-output", payload.lines.join("\n") || "Aucun log disponible.");
}

async function refreshWhitelist() {
  const payload = await apiFetch("/api/whitelist");
  renderWhitelist(payload.names);
}

async function refreshJobs() {
  const payload = await apiFetch("/api/jobs");
  renderJobs(payload.jobs);
}

async function queueAction(path, message) {
  const payload = await apiFetch(path, { method: "POST" });
  showToast(`${message} (${payload.job_id})`);
  await refreshJobs();
}

async function queuePlayerAction(action) {
  const nameInput = document.getElementById("player-name");
  const opInput = document.getElementById("player-op");
  const name = nameInput.value.trim();
  if (!name) {
    showToast("Pseudo requis.", true);
    return;
  }

  const routes = {
    add: { path: "/api/players/add", body: { name, op: opInput.checked }, message: `Ajout de ${name} en file` },
    remove: { path: "/api/players/remove", body: { name }, message: `Retrait de ${name} en file` },
    op: { path: "/api/players/op", body: { name }, message: `OP de ${name} en file` },
    deop: { path: "/api/players/deop", body: { name }, message: `Deop de ${name} en file` },
    onboard: { path: "/api/onboard", body: { name, op: opInput.checked }, message: `Onboarding de ${name} en file` },
  };

  const target = routes[action];
  const payload = await apiFetch(target.path, {
    method: "POST",
    body: JSON.stringify(target.body),
  });
  showToast(`${target.message} (${payload.job_id})`);
  await Promise.all([refreshJobs(), refreshWhitelist()]);
}

function bindEvents() {
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.getAttribute("data-action");
      const labels = {
        start: "Demarrage lance",
        stop: "Arret lance",
        restart: "Restart lance",
        backup: "Backup lance",
      };
      try {
        await queueAction(`/api/actions/${action}`, labels[action]);
      } catch (error) {
        showToast(error.message, true);
      }
    });
  });

  document.querySelectorAll("[data-player-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.getAttribute("data-player-action");
      try {
        await queuePlayerAction(action);
      } catch (error) {
        showToast(error.message, true);
      }
    });
  });

  document.getElementById("refresh-status")?.addEventListener("click", () => refreshStatus().catch((error) => showToast(error.message, true)));
  document.getElementById("refresh-logs")?.addEventListener("click", () => refreshLogs().catch((error) => showToast(error.message, true)));
  document.getElementById("refresh-whitelist")?.addEventListener("click", () => refreshWhitelist().catch((error) => showToast(error.message, true)));
  document.getElementById("refresh-jobs")?.addEventListener("click", () => refreshJobs().catch((error) => showToast(error.message, true)));
  document.getElementById("logout-button")?.addEventListener("click", async () => {
    try {
      await apiFetch("/logout", { method: "POST" });
      window.location.href = "/login";
    } catch (error) {
      showToast(error.message, true);
    }
  });
}

async function initialLoad() {
  try {
    await Promise.all([refreshStatus(), refreshLogs(), refreshWhitelist(), refreshJobs()]);
  } catch (error) {
    showToast(error.message, true);
  }
}

bindEvents();
initialLoad();
window.setInterval(() => refreshJobs().catch(() => {}), 4000);
window.setInterval(() => refreshStatus().catch(() => {}), 8000);
