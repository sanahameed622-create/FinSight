/**
 * Cash Flow Simulator & Stress Testing Controller
 */

let simulationChartInstance = null;

async function runSimulator() {
  const collectionRate = parseFloat(document.getElementById('sim-collection-rate').value) || 80;
  const delayDays = parseInt(document.getElementById('sim-delay-days').value) || 15;
  const defaultRate = parseFloat(document.getElementById('sim-default-rate').value) || 5;
  const horizonWeeks = parseInt(document.getElementById('sim-horizon-weeks').value) || 6;

  // Update slider badge labels
  document.getElementById('val-collection-rate').textContent = `${collectionRate}%`;
  document.getElementById('val-delay-days').textContent = `${delayDays} Days`;
  document.getElementById('val-default-rate').textContent = `${defaultRate}%`;
  document.getElementById('val-horizon-weeks').textContent = `${horizonWeeks} Weeks`;

  try {
    const params = {
      collection_efficiency_pct: collectionRate,
      average_delay_days: delayDays,
      default_risk_pct: defaultRate,
      horizon_weeks: horizonWeeks
    };

    const data = await Api.get('/simulator/run', params);

    // Populate Metrics
    document.getElementById('sim-total-receivables').textContent = formatPKR(data.metrics.total_open_receivables);
    document.getElementById('sim-recoverable-cash').textContent = formatPKR(data.metrics.simulated_recoverable_cash);
    document.getElementById('sim-shortfall').textContent = formatPKR(data.metrics.expected_liquidity_shortfall);
    document.getElementById('sim-bad-debt').textContent = formatPKR(data.metrics.potential_bad_debt);

    // Render Chart
    renderSimulationChart(data.chart_data);

    // Render Recommendations
    const recList = document.getElementById('sim-recommendations-list');
    if (recList) {
      recList.innerHTML = data.recommendations.map(r => `
        <li style="margin-bottom:8px; display:flex; align-items:flex-start; gap:8px;">
          <span style="color:var(--primary); font-weight:bold;">⚡</span>
          <span>${r}</span>
        </li>
      `).join('');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderSimulationChart(chartData) {
  const ctx = document.getElementById('simulationChart');
  if (!ctx || typeof Chart === 'undefined') return;

  if (simulationChartInstance) {
    simulationChartInstance.destroy();
  }

  simulationChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: 'Contractual Baseline Inflow (PKR)',
          data: chartData.baseline_expected,
          borderColor: '#94a3b8',
          backgroundColor: 'rgba(148, 163, 184, 0.1)',
          borderDash: [5, 5],
          tension: 0.3,
          fill: true
        },
        {
          label: 'Stress-Tested Projected Cash Flow (PKR)',
          data: chartData.simulated_scenario,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.15)',
          tension: 0.3,
          fill: true,
          pointRadius: 5,
          pointBackgroundColor: '#2563eb'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (v) => 'Rs. ' + (v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v)
          }
        }
      },
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${formatPKR(ctx.raw)}`
          }
        }
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  runSimulator();

  // Attach input listeners to all sliders
  ['sim-collection-rate', 'sim-delay-days', 'sim-default-rate', 'sim-horizon-weeks'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', runSimulator);
    }
  });
});
