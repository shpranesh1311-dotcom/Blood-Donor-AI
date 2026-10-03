// history.js

async function loadHistory() {
  const wrap = document.getElementById("historyTableWrap");
  showLoading(wrap, "Loading request history...");

  const qs = new URLSearchParams({ limit: 100 });
  const status = document.getElementById("hfStatus").value;
  const urgency = document.getElementById("hfUrgency").value;
  if (status) qs.set("status", status);
  if (urgency) qs.set("urgency", urgency);

  try {
    const reqs = await apiGet(`/api/requests?${qs.toString()}`);
    if (reqs.length === 0) {
      wrap.innerHTML = `<div class="text-muted p-3">No requests match these filters.</div>`;
      return;
    }
    const rows = reqs.map((r) => `
      <tr>
        <td><code>${r.request_id}</code></td>
        <td><strong>${r.blood_group_required}</strong></td>
        <td>${r.units_required}</td>
        <td>${urgencyBadge(r.urgency_level)}</td>
        <td>${r.hospital_area}</td>
        <td>${r.request_datetime}</td>
        <td><span class="badge bg-light text-dark border">${r.request_status}</span></td>
        <td><a class="btn btn-sm btn-outline-danger" href="/search?request_id=${r.request_id}">View Matches</a></td>
      </tr>
    `).join("");

    // Rebuild the table inside the same stable wrapper (may have been
    // replaced by a loading/error/empty state above).
    wrap.innerHTML = `
      <table class="table table-sm table-hover align-middle">
        <thead>
          <tr>
            <th>Request ID</th><th>Blood Group</th><th>Units</th><th>Urgency</th>
            <th>Area</th><th>Requested At</th><th>Status</th><th></th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>`;
  } catch (e) {
    showError(wrap, e.message);
  }
}

document.getElementById("hfBtn").addEventListener("click", loadHistory);
loadHistory();
