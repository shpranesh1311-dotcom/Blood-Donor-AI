// donors.js

async function loadDonors() {
  const wrap = document.getElementById("donorTableWrap");
  const countEl = document.getElementById("dfCount");
  showLoading(wrap, "Loading donors...");

  const qs = new URLSearchParams({ limit: 200 });
  const group = document.getElementById("dfGroup").value;
  const city = document.getElementById("dfCity").value.trim();
  const avail = document.getElementById("dfAvail").value;
  if (group) qs.set("blood_group", group);
  if (city) qs.set("city", city);
  if (avail) qs.set("availability", avail);

  try {
    const donors = await apiGet(`/api/donors?${qs.toString()}`);
    countEl.textContent = `Showing ${donors.length} donor(s) (max 200 rows in demo view)`;

    if (donors.length === 0) {
      wrap.innerHTML = `<div class="text-muted p-3">No donors match these filters.</div>`;
      return;
    }

    const rows = donors.map((d) => `
      <tr>
        <td><code>${d.donor_id}</code></td>
        <td>${d.age}</td>
        <td>${d.gender}</td>
        <td><strong>${d.blood_group}</strong></td>
        <td>${d.city}</td>
        <td>${d.total_donations}</td>
        <td>${d.average_response_time_minutes.toFixed(0)}</td>
        <td>${d.availability_preference}</td>
        <td>${d.current_availability ? '<span class="badge bg-success">Available</span>' : '<span class="badge bg-secondary">Unavailable</span>'}</td>
        <td><span class="badge bg-light text-dark border">${d.donor_status}</span></td>
      </tr>
    `).join("");

    // Rebuild the table inside the same stable wrapper (may have been
    // replaced by a loading/error/empty state above).
    wrap.innerHTML = `
      <table class="table table-sm table-hover align-middle">
        <thead>
          <tr>
            <th>Donor ID</th><th>Age</th><th>Gender</th><th>Blood Group</th><th>City</th>
            <th>Total Donations</th><th>Avg. Response (min)</th><th>Preference</th><th>Availability</th><th>Status</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>`;
  } catch (e) {
    showError(wrap, e.message);
  }
}

document.getElementById("dfSearchBtn").addEventListener("click", loadDonors);
loadDonors();
