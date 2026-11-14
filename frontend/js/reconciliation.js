/**
 * Smart Payment Reconciliation Engine Controller
 */

let openPayments = [];
let openInvoices = [];
let selectedPaymentForManual = null;

async function loadReconciliation() {
  const customerId = document.getElementById('filter-reconcile-customer')?.value || '';

  try {
    // 1. Load summary
    const summary = await Api.get('/reconciliation/summary');
    document.getElementById('rec-total-billed').textContent = formatPKR(summary.total_billed);
    document.getElementById('rec-open-receivables').textContent = formatPKR(summary.total_open_receivables);
    document.getElementById('rec-unallocated-cash').textContent = formatPKR(summary.total_unallocated_cash);
    document.getElementById('rec-rate').textContent = `${summary.reconciliation_rate_percent}%`;

    // 2. Load open items
    const params = customerId ? { customer_id: customerId } : {};
    const items = await Api.get('/reconciliation/open-items', params);

    openPayments = items.unallocated_payments;
    openInvoices = items.open_invoices;

    renderOpenPayments(openPayments);
    renderOpenInvoices(openInvoices);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadCustomersDropdown() {
  try {
    const custs = await Api.get('/customers');
    const select = document.getElementById('filter-reconcile-customer');
    if (select) {
      select.innerHTML = '<option value="">All Accounts (Global)</option>' +
        custs.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    }
  } catch (err) {
    console.error('Error loading customers:', err);
  }
}

function renderOpenPayments(payments) {
  const container = document.getElementById('unallocated-payments-list');
  if (!container) return;

  if (payments.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:32px; color:var(--text-muted); background:#f8fafc; border-radius:var(--radius-md);">
        ✓ All received payments are 100% reconciled!
      </div>
    `;
    return;
  }

  container.innerHTML = payments.map(p => `
    <div class="card" style="margin-bottom:12px; padding:16px; border-left: 4px solid var(--warning);">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
        <div>
          <span style="font-weight:700; color:var(--secondary)">${p.payment_number}</span>
          <span style="font-size:0.8rem; color:var(--text-muted); margin-left:8px;">${p.customer_name}</span>
        </div>
        <span class="badge badge-unallocated">Unallocated</span>
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <div style="font-size:0.75rem; color:var(--text-muted)">${formatDate(p.payment_date)} • ${p.payment_method} ${p.reference_number ? `(${p.reference_number})` : ''}</div>
          <div style="font-size:1.1rem; font-weight:800; color:var(--warning); font-family:monospace">
            ${formatPKR(p.unallocated_amount)} <span style="font-size:0.75rem; color:var(--text-muted)">remaining</span>
          </div>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="openManualReconciliation(${p.id})">
          Manual Match ➔
        </button>
      </div>
    </div>
  `).join('');
}

function renderOpenInvoices(invoices) {
  const container = document.getElementById('open-invoices-list');
  if (!container) return;

  if (invoices.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:32px; color:var(--text-muted); background:#f8fafc; border-radius:var(--radius-md);">
        ✓ No outstanding unpaid invoices found!
      </div>
    `;
    return;
  }

  container.innerHTML = invoices.map(i => `
    <div class="card" style="margin-bottom:12px; padding:16px; border-left: 4px solid ${i.status === 'Overdue' ? 'var(--danger)' : 'var(--primary)'};">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
        <div>
          <span style="font-weight:700; color:var(--secondary)">${i.invoice_number}</span>
          <span style="font-size:0.8rem; color:var(--text-muted); margin-left:8px;">${i.customer_name}</span>
        </div>
        <span class="badge ${i.status === 'Overdue' ? 'badge-overdue' : 'badge-issued'}">${i.status}</span>
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div style="font-size:0.75rem; color:var(--text-muted)">
          Due: ${formatDate(i.due_date)} • Total: ${formatPKR(i.total_amount)}
        </div>
        <div style="font-size:1.1rem; font-weight:800; color:${i.status === 'Overdue' ? 'var(--danger)' : 'var(--secondary)'}; font-family:monospace">
          ${formatPKR(i.balance_due)}
        </div>
      </div>
    </div>
  `).join('');
}

// 1-Click Smart FIFO Auto-Match
async function runAutoFIFOMatch() {
  const customerId = document.getElementById('filter-reconcile-customer')?.value || null;
  const btn = document.getElementById('btn-run-auto-fifo');
  if (btn) btn.disabled = true;

  try {
    const payload = customerId ? { customer_id: parseInt(customerId) } : {};
    const res = await Api.post('/reconciliation/auto-fifo', payload);
    showToast(res.message, 'success');
    loadReconciliation();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

// Manual Reconciliation Modal
function openManualReconciliation(paymentId) {
  selectedPaymentForManual = openPayments.find(p => p.id === paymentId);
  if (!selectedPaymentForManual) return;

  document.getElementById('manual-rec-pay-num').textContent = selectedPaymentForManual.payment_number;
  document.getElementById('manual-rec-customer').textContent = selectedPaymentForManual.customer_name;
  document.getElementById('manual-rec-amount').textContent = formatPKR(selectedPaymentForManual.unallocated_amount);

  // Filter invoices belonging to this customer only
  const custInvoices = openInvoices.filter(i => i.customer_id === selectedPaymentForManual.customer_id);
  const container = document.getElementById('manual-rec-invoices-container');

  if (custInvoices.length === 0) {
    container.innerHTML = `<div style="padding:16px; color:var(--text-muted)">No open invoices found for ${selectedPaymentForManual.customer_name}.</div>`;
  } else {
    container.innerHTML = custInvoices.map(inv => `
      <div style="display:flex; justify-content:space-between; align-items:center; padding:12px; border-bottom:1px solid var(--border-color);">
        <div>
          <div style="font-weight:700">${inv.invoice_number}</div>
          <div style="font-size:0.75rem; color:var(--text-muted)">Due: ${formatDate(inv.due_date)} • Balance Due: ${formatPKR(inv.balance_due)}</div>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <input type="number" 
            class="form-control manual-alloc-input" 
            data-invoice-id="${inv.id}" 
            data-max="${Math.min(selectedPaymentForManual.unallocated_amount, inv.balance_due)}"
            placeholder="PKR 0" 
            max="${Math.min(selectedPaymentForManual.unallocated_amount, inv.balance_due)}" 
            min="0" 
            style="width:140px; text-align:right" />
          <button type="button" class="btn btn-secondary btn-sm" onclick="fillMaxAllocation(this, ${Math.min(selectedPaymentForManual.unallocated_amount, inv.balance_due)})">
            Max
          </button>
        </div>
      </div>
    `).join('');
  }

  openModal('modal-manual-reconcile');
}

function fillMaxAllocation(btn, maxVal) {
  const input = btn.previousElementSibling;
  input.value = maxVal;
}

async function submitManualReconciliation() {
  if (!selectedPaymentForManual) return;

  const inputs = document.querySelectorAll('.manual-alloc-input');
  const allocations = [];

  inputs.forEach(inp => {
    const amt = parseFloat(inp.value) || 0;
    if (amt > 0) {
      allocations.push({
        invoice_id: parseInt(inp.dataset.invoiceId),
        amount_to_allocate: amt
      });
    }
  });

  if (allocations.length === 0) {
    showToast('Please specify an amount to allocate to at least one invoice.', 'warning');
    return;
  }

  try {
    const payload = {
      payment_id: selectedPaymentForManual.id,
      allocations: allocations
    };
    const res = await Api.post('/reconciliation/manual', payload);
    showToast(res.message, 'success');
    closeModal('modal-manual-reconcile');
    loadReconciliation();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadReconciliation();
  loadCustomersDropdown();

  const filterSelect = document.getElementById('filter-reconcile-customer');
  if (filterSelect) filterSelect.addEventListener('change', () => loadReconciliation());

  const btnAuto = document.getElementById('btn-run-auto-fifo');
  if (btnAuto) btnAuto.addEventListener('click', runAutoFIFOMatch);

  const btnSubmitManual = document.getElementById('btn-submit-manual-rec');
  if (btnSubmitManual) btnSubmitManual.addEventListener('click', submitManualReconciliation);
});
