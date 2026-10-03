// predict.js

document.getElementById("predictForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const resultEl = document.getElementById("predictResult");
  showLoading(resultEl, "Running model inference...");

  const payload = {
    age: parseInt(document.getElementById("pAge").value, 10),
    blood_group: document.getElementById("pGroup").value,
    total_donations: parseInt(document.getElementById("pTotalDon").value, 10),
    previous_requests_received: parseInt(document.getElementById("pReceived").value, 10),
    previous_requests_responded: parseInt(document.getElementById("pResponded").value, 10),
    average_response_time_minutes: parseFloat(document.getElementById("pAvgTime").value),
    current_availability: document.getElementById("pAvail").checked,
    distance_km: parseFloat(document.getElementById("pDistance").value),
    urgency_level: document.getElementById("pUrgency").value,
    units_required: parseInt(document.getElementById("pUnits").value, 10),
  };

  try {
    const result = await apiPost("/api/predict", payload);
    renderPrediction(result);
  } catch (err) {
    showError(resultEl, err.message);
  }
});

function renderPrediction(result) {
  const resultEl = document.getElementById("predictResult");
  const pctVal = Math.round(result.response_probability * 100);
  const color = pctVal >= 70 ? "#1e9e6b" : pctVal >= 40 ? "#d9862c" : "#c0263d";

  const factorsHtml = result.top_factors.map((f) => `
    <span class="factor-chip factor-${f.impact}">
      ${f.factor}: <strong>${f.value}</strong>
    </span>
  `).join("");

  resultEl.innerHTML = `
    <h6 class="text-muted mb-2">Predicted Response Probability</h6>
    <div class="display-3 fw-bold mb-1" style="color:${color}">${pctVal}%</div>
    <p class="fw-semibold mb-3">${result.classification}</p>
    <div class="text-start">
      <h6 class="fw-bold mt-4 mb-2">Contributing Factors</h6>
      <div>${factorsHtml}</div>
    </div>
    <div class="alert alert-secondary small mt-4 mb-0 text-start">${result.disclaimer}</div>
  `;
}
