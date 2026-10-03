// request.js

const DEFAULT_LAT = 11.0016;
const DEFAULT_LON = 76.9558;
let selectedLat = DEFAULT_LAT;
let selectedLon = DEFAULT_LON;

const pickMap = L.map("pickMap").setView([DEFAULT_LAT, DEFAULT_LON], 12);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(pickMap);

let marker = L.marker([DEFAULT_LAT, DEFAULT_LON]).addTo(pickMap);

pickMap.on("click", (e) => {
  selectedLat = e.latlng.lat;
  selectedLon = e.latlng.lng;
  marker.setLatLng(e.latlng);
  document.getElementById("coordsLabel").textContent = `${selectedLat.toFixed(4)}, ${selectedLon.toFixed(4)}`;
});

document.getElementById("requestForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const resultArea = document.getElementById("resultArea");
  showLoading(resultArea, "Creating request and running AI matching...");

  const payload = {
    blood_group_required: document.getElementById("bloodGroup").value,
    units_required: parseInt(document.getElementById("units").value, 10),
    urgency_level: document.getElementById("urgency").value,
    hospital_area: document.getElementById("area").value,
    latitude: selectedLat,
    longitude: selectedLon,
    notes: document.getElementById("notes").value || null,
  };

  try {
    const created = await apiPost("/api/requests", payload);
    const matchResult = await apiPost(`/api/match/${created.request_id}?top_n=10`, {});
    renderResult(created, matchResult);
  } catch (err) {
    showError(resultArea, err.message);
  }
});

function renderResult(request, matchResult) {
  const resultArea = document.getElementById("resultArea");

  let rows = matchResult.matches.map((m) => `
    <tr>
      <td><span class="rank-badge">${m.rank}</span></td>
      <td><code>${m.donor_id}</code></td>
      <td><strong>${m.blood_group}</strong></td>
      <td>${m.city}</td>
      <td>${m.distance_km} km</td>
      <td>${pct(m.ml_response_probability)}</td>
      <td>${responseBadge(m.expected_response_label)}</td>
      <td>
        <div class="score-bar-bg mb-1"><div class="score-bar-fill" style="width:${m.overall_score}%"></div></div>
        <small class="text-muted">${m.overall_score}/100</small>
      </td>
      <td><button class="btn btn-sm btn-outline-danger" onclick="notifyDonor('${m.donor_id}','${request.request_id}',this)">Notify Donor</button></td>
    </tr>
  `).join("");

  if (matchResult.matches.length === 0) {
    rows = `<tr><td colspan="9" class="text-muted">No eligible donors found within the configured search radius. Try widening the radius in eligibility_config.json.</td></tr>`;
  }

  resultArea.innerHTML = `
    <div class="d-flex justify-content-between align-items-start mb-3">
      <div>
        <h5 class="mb-1">Request <code>${request.request_id}</code> created</h5>
        <p class="text-muted mb-0">
          ${matchResult.total_compatible_donors} blood-compatible donors found &rarr;
          ${matchResult.total_eligible_donors} passed demo eligibility rules &rarr;
          top ${matchResult.matches.length} ranked below.
        </p>
      </div>
      <span class="badge badge-urgency-${request.urgency_level} fs-6">${request.urgency_level}</span>
    </div>
    <div class="table-responsive">
      <table class="table table-hover align-middle">
        <thead>
          <tr>
            <th>Rank</th><th>Donor</th><th>Group</th><th>Area</th><th>Distance</th>
            <th>Response Prob.</th><th>Expected Speed</th><th>Overall Score</th><th></th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <div class="alert alert-secondary small mt-3 mb-0">${matchResult.disclaimer}</div>
  `;
}

async function notifyDonor(donorId, requestId, btn) {
  btn.disabled = true;
  btn.textContent = "Notifying...";
  try {
    const res = await apiPost(`/api/notify/${donorId}?request_id=${requestId}`, {});
    btn.textContent = "Notified ✓";
    btn.classList.remove("btn-outline-danger");
    btn.classList.add("btn-success");
  } catch (e) {
    btn.disabled = false;
    btn.textContent = "Notify Donor";
    alert(e.message);
  }
}
