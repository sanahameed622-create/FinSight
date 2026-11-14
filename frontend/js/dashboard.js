/**
 * Dashboard Controller
 */

let cashFlowChartInstance = null;
let agingChartInstance = null;

async function loadDashboard() {
  try {
    const data = await Api.get('/dashboard/stats');

    // 1. Populate KPI values
    document.getElementById('kpi-receivables').textContent = formatPKR(data.kpis.total_receivables);
    document.getElementById('kpi-collections').textContent = formatPKR(data.kpis.collections_this_month);
    document.getElementById('kpi-overdue').textContent = formatPKR(data.kpis.overdue_receivables);
    document.getElementById('kpi-unallocated').textContent = formatPKR(data.kpis.unallocated_cash);

    // Show/Hide Sample Data Banner if workspace has zero customers
    const bannerEl = document.getElementById('sample-data-banner');
    const topBtn = document.getElementById('btn-topbar-sample');
    if (data.kpis.active_customers_count === 0 && data.kpis.total_receivables === 0) {
      if (bannerEl) bannerEl.style.display = 'block';
      if (topBtn) topBtn.style.display = 'inline-flex';
    } else {
      if (bannerEl) bannerEl.style.display = 'none';
      if (topBtn) topBtn.style.display = 'none';
    }

    // 2. AI Financial Intelligence & Health
    renderAIInsights(data.ai_insights);

    // 3. Render Charts
    renderCashFlowChart(data.cash_flow_trend);
    renderAgingChart(data.aging_distribution);

    // 4. Recent Activities
    renderRecentActivities(data.recent_activities);

  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderAIInsights(ai) {
  const scoreEl = document.getElementById('ai-health-score');
  const statusEl = document.getElementById('ai-health-status');
  const listEl = document.getElementById('ai-insights-list');

  if (scoreEl) scoreEl.textContent = `${ai.health_score}/100`;
  if (statusEl) statusEl.textContent = ai.status;

  if (listEl) {
    if (!ai.insights || ai.insights.length === 0) {
      listEl.innerHTML = `<div class="insight-item"><p>No critical risks detected. Operations running smoothly.</p></div>`;
      return;
    }

    listEl.innerHTML = ai.insights.map(item => `
      <div class="insight-item">
        <div>
          <div class="insight-item-header">
            <span class="insight-title">${item.title}</span>
            <span class="insight-metric">${item.metric}</span>
          </div>
          <p class="insight-desc">${item.message}</p>
        </div>
        ${item.action === 'AUTO_RECONCILE' ? `
          <button class="btn btn-accent btn-sm" onclick="triggerDashboardReconcile()" style="align-self: flex-start; margin-top: 8px;">
            ⚡ 1-Click Auto Reconcile
          </button>
        ` : ''}
      </div>
    `).join('');
  }
}

async function triggerDashboardReconcile() {
  try {
    const res = await Api.post('/reconciliation/auto-fifo', {});
    showToast(res.message, 'success');
    loadDashboard(); // Refresh
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderCashFlowChart(trend) {
  const ctx = document.getElementById('cashFlowChart');
  if (!ctx || typeof Chart === 'undefined') return;

  if (cashFlowChartInstance) {
    cashFlowChartInstance.destroy();
  }

  cashFlowChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: trend.labels,
      datasets: [
        {
          label: 'Invoiced (PKR)',
          data: trend.invoiced,
          backgroundColor: '#3b82f6',
          borderRadius: 4
        },
        {
          label: 'Collected (PKR)',
          data: trend.collected,
          backgroundColor: '#10b981',
          borderRadius: 4
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

function renderAgingChart(aging) {
  const ctx = document.getElementById('agingChart');
  if (!ctx || typeof Chart === 'undefined') return;

  if (agingChartInstance) {
    agingChartInstance.destroy();
  }

  agingChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Current (0-30d)', 'Overdue 31-60d', 'Overdue 61-90d', 'Overdue 90+d'],
      datasets: [{
        data: [
          aging.current_0_30,
          aging.overdue_31_60,
          aging.overdue_61_90,
          aging.overdue_90_plus
        ],
        backgroundColor: ['#10b981', '#f59e0b', '#f97316', '#ef4444'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.label}: ${formatPKR(ctx.raw)}`
          }
        }
      }
    }
  });
}

function renderRecentActivities(activities) {
  const listEl = document.getElementById('recent-activities-list');
  if (!listEl) return;

  if (!activities || activities.length === 0) {
    listEl.innerHTML = '<p style="color:var(--text-muted); padding:16px 0;">No recent activities logged.</p>';
    return;
  }

  listEl.innerHTML = activities.map(act => `
    <div class="activity-item">
      <div class="activity-dot"></div>
      <div class="activity-details">
        <div class="activity-text">${act.description}</div>
        <div class="activity-time">${act.time}</div>
      </div>
    </div>
  `).join('');
}

async function loadSampleFMCGData() {
  const btn = document.getElementById('btn-banner-load-sample');
  const topBtn = document.getElementById('btn-topbar-sample');
  
  if (!confirm('Would you like to populate your workspace with sample Pakistani FMCG distributors (Lahore Super Mart, Madina Cash & Carry), stock products, invoices, and post-dated cheques?')) {
    return;
  }

  try {
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span>⏳</span><span>Loading Sample Data...</span>';
    }
    if (topBtn) {
      topBtn.disabled = true;
      topBtn.innerHTML = '<span>⏳</span><span>Loading...</span>';
    }

    const res = await Api.post('/dashboard/load-sample-data', {});
    showToast(res.message, res.success ? 'success' : 'info');
    
    // Reload dashboard with fresh sample data
    await loadDashboard();
  } catch (err) {
    showToast(err.message || 'Failed to load sample data', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<span>⚡</span><span>Load Sample FMCG Data</span>';
    }
    if (topBtn) {
      topBtn.disabled = false;
      topBtn.innerHTML = '<span>✨</span><span>Load Sample Data</span>';
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
});
