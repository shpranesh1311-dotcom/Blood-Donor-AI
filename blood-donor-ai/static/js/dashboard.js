// dashboard.js

function statCard(value, label, colorClass) {
  return `
    <div class="col-6 col-lg-2">
      <div class="stat-card">
        <div class="stat-value ${colorClass || ''}">${value}</div>
        <div class="stat-label">${label}</div>
      </div>
    </div>`;
}

async function loadStats() {
  const cardsEl = document.getElementById("statCards");
  try {
    const stats = await apiGet("/api/dashboard/stats");

    cardsEl.innerHTML =
      statCard(stats.total_donors.toLocaleString(), "Total Donors") +
      statCard(stats.available_donors.toLocaleString(), "Available Now") +
      statCard(stats.active_requests.toLocaleString(), "Active Requests") +
      statCard(stats.critical_requests.toLocaleString(), "Critical Requests", "text-danger") +
      statCard(stats.successful_matches.toLocaleString(), "Fulfilled Requests", "text-success");

    document.getElementById("responseRateVal").textContent = pct(stats.overall_response_rate);
    document.getElementById("avgResponseVal").textContent = `${stats.avg_response_time_minutes} min`;

    renderPieChart("chartBloodGroup", stats.donors_by_blood_group);
    renderDoughnut("chartAvailability", stats.availability_split, ["#1e9e6b", "#c0263d"]);
    renderPieChart("chartUrgency", stats.requests_by_urgency, ["#c0263d", "#d9862c", "#4b7bec", "#8d9199"]);
    renderLineChart("chartMonthly", stats.monthly_requests);
  } catch (e) {
    showError(cardsEl, e.message);
  }
}

function renderPieChart(canvasId, dataObj, colors) {
  const ctx = document.getElementById(canvasId);
  new Chart(ctx, {
    type: "pie",
    data: {
      labels: Object.keys(dataObj),
      datasets: [{ data: Object.values(dataObj), backgroundColor: colors || defaultPalette(Object.keys(dataObj).length) }],
    },
    options: { plugins: { legend: { position: "bottom" } } },
  });
}

function renderDoughnut(canvasId, dataObj, colors) {
  const ctx = document.getElementById(canvasId);
  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: Object.keys(dataObj),
      datasets: [{ data: Object.values(dataObj), backgroundColor: colors }],
    },
    options: { plugins: { legend: { position: "bottom" } } },
  });
}

function renderLineChart(canvasId, dataObj) {
  const ctx = document.getElementById(canvasId);
  new Chart(ctx, {
    type: "line",
    data: {
      labels: Object.keys(dataObj),
      datasets: [{
        label: "Emergency Requests",
        data: Object.values(dataObj),
        borderColor: "#c0263d",
        backgroundColor: "rgba(192,38,61,0.15)",
        tension: 0.35,
        fill: true,
      }],
    },
    options: { plugins: { legend: { display: false } } },
  });
}

function defaultPalette(n) {
  const base = ["#c0263d", "#d9862c", "#4b7bec", "#1e9e6b", "#8d9199", "#9b59b6", "#16a085", "#e67e22"];
  return Array.from({ length: n }, (_, i) => base[i % base.length]);
}

async function loadRecentRequests() {
  const body = document.getElementById("recentRequestsBody");
  try {
    const reqs = await apiGet("/api/requests?limit=8");
    if (reqs.length === 0) {
      body.innerHTML = `<tr><td colspan="8" class="text-muted">No emergency requests yet.</td></tr>`;
      return;
    }
    const rows = await Promise.all(reqs.map(async (r) => {
      let compatibleCount = "—";
      try {
        const donors = await apiGet(`/api/donors?compatible_with=${r.blood_group_required}&limit=500`);
        compatibleCount = donors.length;
      } catch (e) { /* ignore */ }
      return `
        <tr>
          <td><code>${r.request_id}</code></td>
          <td><strong>${r.blood_group_required}</strong></td>
          <td>${r.units_required}</td>
          <td>${urgencyBadge(r.urgency_level)}</td>
          <td>${r.hospital_area}</td>
          <td><span class="badge bg-secondary">${r.request_status}</span></td>
          <td>${compatibleCount}</td>
          <td><a href="/search?request_id=${r.request_id}" class="btn btn-sm btn-outline-danger">Match</a></td>
        </tr>`;
    }));
    body.innerHTML = rows.join("");
  } catch (e) {
    showError(body.parentElement.parentElement, e.message);
  }
}

loadStats();
loadRecentRequests();
