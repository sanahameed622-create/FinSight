/**
 * Financial Reports Controller
 */

async function loadAgingReport() {
  try {
    const data = await Api.get('/reports/aging');

    // Populate summary
    document.getElementById('aging-current-sum').textContent = formatPKR(data.summary.current_0_30);
    document.getElementById('aging-30-sum').textContent = formatPKR(data.summary.overdue_31_60);
    document.getElementById('aging-60-sum').textContent = formatPKR(data.summary.overdue_61_90);
    document.getElementById('aging-90-sum').textContent = formatPKR(data.summary.overdue_90_plus);
    document.getElementById('aging-grand-total').textContent = formatPKR(data.summary.grand_total_receivables);

    // Populate table
    const tbody = document.getElementById('aging-report-tbody');
    if (tbody) {
      if (!data.customers || data.customers.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:32px; color:var(--text-muted)">No accounts receivable balance found.</td></tr>`;
      } else {
        tbody.innerHTML = data.customers.map(c => `
          <tr>
            <td>
              <div style="font-weight:700; color:var(--secondary)">${c.customer_name}</div>
              <div style="font-size:0.75rem; color:var(--text-muted)">${c.company_name} • ${c.phone}</div>
            </td>
            <td class="amount" style="color:var(--accent)">${formatPKR(c.current)}</td>
            <td class="amount" style="color:${c.days_31_60 > 0 ? 'var(--warning)' : 'inherit'}">${formatPKR(c.days_31_60)}</td>
            <td class="amount" style="color:${c.days_61_90 > 0 ? '#ea580c' : 'inherit'}">${formatPKR(c.days_61_90)}</td>
            <td class="amount" style="color:${c.days_90_plus > 0 ? 'var(--danger)' : 'inherit'}; font-weight:700">${formatPKR(c.days_90_plus)}</td>
            <td class="amount" style="font-weight:800; font-family:monospace">${formatPKR(c.total_due)}</td>
            <td>
              <span class="badge ${c.risk_level === 'High' ? 'badge-overdue' : (c.risk_level === 'Medium' ? 'badge-partially-paid' : 'badge-paid')}">
                ${c.risk_level} Risk
              </span>
            </td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadCustomersForStatement() {
  try {
    const custs = await Api.get('/customers');
    const select = document.getElementById('report-khata-customer-select');
    if (select) {
      select.innerHTML = '<option value="">-- Choose Customer to Generate Statement of Account --</option>' +
        custs.map(c => `<option value="${c.id}">${c.name} (${c.city || 'City'})</option>`).join('');
    }
  } catch (err) {
    console.error('Error loading customers for report:', err);
  }
}

async function fetchStatement() {
  const customerId = document.getElementById('report-khata-customer-select')?.value;
  if (!customerId) {
    showToast('Please select a customer first.', 'warning');
    return;
  }

  try {
    const data = await Api.get(`/reports/ledger/${customerId}`);
    document.getElementById('khata-customer-header').style.display = 'block';
    document.getElementById('khata-cust-title').textContent = `${data.customer.name} - Statement of Account`;
    document.getElementById('khata-invoiced-val').textContent = formatPKR(data.summary.total_invoiced);
    document.getElementById('khata-paid-val').textContent = formatPKR(data.summary.total_paid);
    document.getElementById('khata-outstanding-val').textContent = formatPKR(data.summary.net_outstanding);

    const tbody = document.getElementById('khata-statement-tbody');
    if (!data.statement || data.statement.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-muted)">No statement transactions found.</td></tr>`;
    } else {
      tbody.innerHTML = data.statement.map(item => `
        <tr>
          <td>${formatDate(item.date)}</td>
          <td><span class="badge ${item.type === 'INVOICE' ? 'badge-issued' : 'badge-paid'}">${item.type}</span></td>
          <td style="font-weight:600">${item.reference}</td>
          <td>${item.description}</td>
          <td class="amount">${item.debit > 0 ? formatPKR(item.debit) : '-'}</td>
          <td class="amount" style="color:var(--accent)">${item.credit > 0 ? formatPKR(item.credit) : '-'}</td>
          <td class="amount" style="font-weight:700">${formatPKR(item.running_balance)}</td>
        </tr>
      `).join('');
    }

    const exportBtn = document.getElementById('btn-export-current-khata');
    if (exportBtn) {
      exportBtn.onclick = () => {
        window.open(`/api/reports/export/ledger?customer_id=${customerId}`, '_blank');
      };
    }

    const whatsappBtn = document.getElementById('btn-whatsapp-report-statement');
    if (whatsappBtn) {
      whatsappBtn.onclick = () => {
        const rawPhone = data.customer.phone || '';
        let cleanPhone = rawPhone.replace(/\D/g, '');
        if (cleanPhone.startsWith('0')) cleanPhone = '92' + cleanPhone.substring(1);
        const msg = `Dear ${data.customer.name},\n\nPlease find your updated Statement of Account with ${Api.getBusinessName()}:\n• Total Billed: ${formatPKR(data.summary.total_invoiced)}\n• Payments Received: ${formatPKR(data.summary.total_paid)}\n• Current Outstanding Balance: ${formatPKR(data.summary.net_outstanding)}\n\nPlease settle via Raast / Bank Wire.\nThank you!`;
        const url = `https://api.whatsapp.com/send?phone=${cleanPhone}&text=${encodeURIComponent(msg)}`;
        window.open(url, '_blank');
      };
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function exportReport(type) {
  window.open(`/api/reports/export/${type}`, '_blank');
}

document.addEventListener('DOMContentLoaded', () => {
  loadAgingReport();
  loadCustomersForStatement();

  const btnFetchStatement = document.getElementById('btn-fetch-khata');
  if (btnFetchStatement) btnFetchStatement.addEventListener('click', fetchStatement);
});
