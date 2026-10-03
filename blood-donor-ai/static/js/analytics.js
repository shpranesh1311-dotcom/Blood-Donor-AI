// analytics.js

function palette(n) {
  const base = ["#c0263d", "#d9862c", "#4b7bec", "#1e9e6b", "#8d9199", "#9b59b6", "#16a085", "#e67e22"];
  return Array.from({ length: n }, (_, i) => base[i % base.length]);
}

async function loadAnalytics() {
  try {
    const data = await apiGet("/api/dashboard/analytics");

    new Chart(document.getElementById("chartRateByGroup"), {
      type: "bar",
      data: {
        labels: Object.keys(data.response_rate_by_blood_group),
        datasets: [{
          label: "Response rate",
          data: Object.values(data.response_rate_by_blood_group).map((v) => Math.round(v * 100)),
          backgroundColor: palette(Object.keys(data.response_rate_by_blood_group).length),
        }],
      },
      options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { callback: (v) => v + "%" } } } },
    });

    new Chart(document.getElementById("chartRateByUrgency"), {
      type: "bar",
      data: {
        labels: Object.keys(data.response_rate_by_urgency),
        datasets: [{
          label: "Response rate",
          data: Object.values(data.response_rate_by_urgency).map((v) => Math.round(v * 100)),
          backgroundColor: ["#c0263d", "#d9862c", "#4b7bec", "#8d9199"],
        }],
      },
      options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { callback: (v) => v + "%" } } } },
    });

    new Chart(document.getElementById("chartTimeDist"), {
      type: "bar",
      data: {
        labels: Object.keys(data.response_time_distribution),
        datasets: [{
          label: "Responses",
          data: Object.values(data.response_time_distribution),
          backgroundColor: "#4b7bec",
        }],
      },
      options: { plugins: { legend: { display: false } } },
    });

    document.getElementById("matchStats").innerHTML = `
      <p class="mb-2">Total AI-generated matches to date: <strong>${data.total_matches_generated.toLocaleString()}</strong></p>
      <p class="mb-0">Average overall ranking score: <strong>${data.avg_match_score} / 100</strong></p>
    `;

    const mm = data.model_metrics;
    if (mm && mm.calibrated_metrics) {
      const cm = mm.calibrated_metrics;
      document.getElementById("modelMetrics").innerHTML = `
        <p class="mb-1">Best model: <strong>${mm.best_model_name}</strong> (calibrated)</p>
        <ul class="list-unstyled small mb-0">
          <li>Accuracy: <strong>${cm.accuracy}</strong></li>
          <li>Precision: <strong>${cm.precision}</strong></li>
          <li>Recall: <strong>${cm.recall}</strong></li>
          <li>F1-score: <strong>${cm.f1_score}</strong></li>
          <li>ROC-AUC: <strong>${cm.roc_auc}</strong></li>
        </ul>
        <p class="text-muted small mt-2 mb-0">Trained on ${mm.training_rows.toLocaleString()} rows, tested on ${mm.test_rows.toLocaleString()} rows.</p>
      `;
    } else {
      document.getElementById("modelMetrics").innerHTML = `<p class="mb-0">Model metadata not found. Run <code>python ml/train.py</code>.</p>`;
    }
  } catch (e) {
    document.getElementById("matchStats").innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
  }
}

loadAnalytics();
