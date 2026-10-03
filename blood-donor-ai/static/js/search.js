// search.js

const DEFAULT_LAT = 11.0016;
const DEFAULT_LON = 76.9558;
let searchLat = DEFAULT_LAT;
let searchLon = DEFAULT_LON;

const searchMap = L.map("searchMap").setView([DEFAULT_LAT, DEFAULT_LON], 12);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(searchMap);
let centerMarker = L.marker([DEFAULT_LAT, DEFAULT_LON]).addTo(searchMap);
let resultMarkers = [];

searchMap.on("click", (e) => {
  searchLat = e.latlng.lat;
  searchLon = e.latlng.lng;
  centerMarker.setLatLng(e.latlng);
});

document.getElementById("fDistance").addEventListener("input", (e) => {
  document.getElementById("distVal").textContent = e.target.value;
});
document.getElementById("fProb").addEventListener("input", (e) => {
  document.getElementById("probVal").textContent = `${e.target.value}%`;
});

// Pre-fill from ?request_id= if navigated from the dashboard "Match" button
const params = new URLSearchParams(window.location.search);
const prefilledRequestId = params.get("request_id");

async function runSearch() {
  const resultsEl = document.getElementById("searchResults");
  showLoading(resultsEl, "Running AI matching...");

  const qs = new URLSearchParams({
    blood_group_required: document.getElementById("fBloodGroup").value,
    latitude: searchLat,
    longitude: searchLon,
    urgency_level: document.getElementById("fUrgency").value,
    max_distance_km: document.getElementById("fDistance").value,
    min_probability: (parseInt(document.getElementById("fProb").value, 10) / 100).toFixed(2),
    availability_only: document.getElementById("fAvailOnly").checked,
  });
  const city = document.getElementById("fCity").value.trim();
  if (city) qs.set("city", city);

  try {
    const result = await apiGet(`/api/search-donors?${qs.toString()}`);
    renderResults(result);
  } catch (e) {
    showError(resultsEl, e.message);
  }
}

function renderResults(result) {
  const resultsEl = document.getElementById("searchResults");

  resultMarkers.forEach((m) => searchMap.removeLayer(m));
  resultMarkers = [];

  if (result.matches.length === 0) {
    resultsEl.innerHTML = `
      <div class="alert alert-warning mb-0">
        No eligible, compatible donors found with the current filters.
        Total compatible by blood group: ${result.total_compatible_donors}, eligible: ${result.total_eligible_donors}.
        Try widening distance or lowering the minimum response probability.
      </div>`;
    return;
  }

  const rows = result.matches.map((m) => `
    <tr>
      <td><span class="rank-badge">${m.rank}</span></td>
      <td><code>${m.donor_id}</code></td>
      <td><strong>${m.blood_group}</strong></td>
      <td>${m.city}</td>
      <td>${m.distance_km} km</td>
      <td>${pct(m.ml_response_probability)}</td>
      <td>${m.current_availability ? '<span class="badge bg-success">Available</span>' : '<span class="badge bg-secondary">Unavailable</span>'}</td>
      <td>${responseBadge(m.expected_response_label)}</td>
      <td>
        <div class="score-bar-bg mb-1"><div class="score-bar-fill" style="width:${m.overall_score}%"></div></div>
        <small class="text-muted">${m.overall_score}/100</small>
      </td>
      <td><button class="btn btn-sm btn-outline-danger" onclick="notifyDonor('${m.donor_id}', this)">Notify</button></td>
    </tr>
  `).join("");

  resultsEl.innerHTML = `
    <p class="text-muted">
      ${result.total_compatible_donors} compatible &rarr; ${result.total_eligible_donors} eligible &rarr;
      showing top ${result.matches.length} ranked donors.
    </p>
    <div class="table-responsive">
      <table class="table table-hover align-middle">
        <thead>
          <tr>
            <th>Rank</th><th>Donor</th><th>Group</th><th>Area</th><th>Distance</th>
            <th>Response Prob.</th><th>Availability</th><th>Speed</th><th>Score</th><th></th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <div class="alert alert-secondary small mb-0">${result.disclaimer}</div>
  `;
}

async function notifyDonor(donorId, btn) {
  btn.disabled = true;
  btn.textContent = "...";
  try {
    await apiPost(`/api/notify/${donorId}?request_id=SEARCH`, {});
    btn.textContent = "Notified ✓";
    btn.classList.remove("btn-outline-danger");
    btn.classList.add("btn-success");
  } catch (e) {
    btn.disabled = false;
    btn.textContent = "Notify";
    alert(e.message);
  }
}

document.getElementById("searchBtn").addEventListener("click", runSearch);

if (prefilledRequestId) {
  apiGet(`/api/requests/${prefilledRequestId}`).then((req) => {
    document.getElementById("fBloodGroup").value = req.blood_group_required;
    document.getElementById("fUrgency").value = req.urgency_level;
    searchLat = req.latitude;
    searchLon = req.longitude;
    centerMarker.setLatLng([searchLat, searchLon]);
    searchMap.setView([searchLat, searchLon], 12);
    runSearch();
  }).catch(() => {});
}
