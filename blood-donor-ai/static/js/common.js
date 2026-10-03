// common.js - shared helpers used across pages

async function apiGet(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

async function apiPost(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data || {}),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg = body.error || body.detail || `Request failed (${res.status})`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return res.json();
}

function urgencyBadge(urgency) {
  return `<span class="badge badge-urgency-${urgency}">${urgency}</span>`;
}

function responseBadge(label) {
  return `<span class="badge badge-response-${label}">${label}</span>`;
}

function pct(x) {
  return `${Math.round(x * 100)}%`;
}

function showError(containerEl, message) {
  containerEl.innerHTML = `<div class="alert alert-danger" role="alert">⚠️ ${message}</div>`;
}

function showLoading(containerEl, text) {
  containerEl.innerHTML = `<div class="d-flex align-items-center gap-2 text-muted py-3"><div class="loader"></div><span>${text || "Loading..."}</span></div>`;
}
