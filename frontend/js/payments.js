/**
 * Payments & Post-Dated Cheques (PDC) Controller
 */

let allPayments = [];
let allCheques = [];
let availableCustomers = [];
let currentActiveTab = 'payments';

function switchPaymentTab(tab) {
  currentActiveTab = tab;
  const btnPayments = document.getElementById('tab-btn-payments');
  const btnCheques = document.getElementById('tab-btn-cheques');
  const panePayments = document.getElementById('pane-payments');
  const paneCheques = document.getElementById('pane-cheques');

  if (tab === 'payments') {
    btnPayments.classList.add('active');
    btnCheques.classList.remove('active');
    panePayments.style.display = 'block';
    paneCheques.style.display = 'none';
    loadPayments();
  } else {
    btnPayments.classList.remove('active');
    btnCheques.classList.add('active');
    panePayments.style.display = 'none';
    paneCheques.style.display = 'block';
    loadCheques();
  }
}

async function loadPayments() {
  const search = document.getElementById('search-payment')?.value || '';
  const status = document.getElementById('filter-status')?.value || '';

  try {
    const params = {};
    if (search) params.search = search;
    if (status && status !== 'All') params.status = status;

    allPayments = await Api.get('/payments', params);
    renderPaymentsTable(allPayments);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadCheques() {
  try {
    allCheques = await Api.get('/cheques');
    renderChequesTable(allCheques);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadCustomersDropdown() {
  try {
    availableCustomers = await Api.get('/customers');
    const pSelect = document.getElementById('payment-customer-select');
    const cSelect = document.getElementById('cheque-customer-select');

    const options = '<option value="">-- Select Customer Account --</option>' +
      availableCustomers.map(c => `<option value="${c.id}">${c.name} (${c.city || 'City'})</option>`).join('');

    if (pSelect) pSelect.innerHTML = options;
    if (cSelect) cSelect.innerHTML = options;
  } catch (err) {
    console.error('Error loading customers for dropdown:', err);
  }
}

function renderPaymentsTable(payments) {
  const tbody = document.getElementById('payments-tbody');
  if (!tbody) return;

  if (payments.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:32px; color:var(--text-muted)">No payment records found.</td></tr>`;
    return;
  }

  tbody.innerHTML = payments.map(p => {
    let badgeClass = 'badge-reconciled';
    if (p.status === 'Unallocated') badgeClass = 'badge-unallocated';
    else if (p.status === 'Partially Allocated') badgeClass = 'badge-partially-paid';

    return `
      <tr>
        <td style="font-weight:700; color:var(--accent)">${p.payment_number}</td>
        <td>${p.customer_name}</td>
        <td>${formatDate(p.payment_date)}</td>
        <td>
          <span style="font-weight:600">${p.payment_method}</span>
          ${p.reference_number ? `<div style="font-size:0.75rem; color:var(--text-muted)">Ref: ${p.reference_number}</div>` : ''}
        </td>
        <td class="amount">${formatPKR(p.amount)}</td>
        <td class="amount" style="color: ${p.unallocated_amount > 0 ? 'var(--warning)' : 'var(--text-muted)'}; font-weight:700">
          ${formatPKR(p.unallocated_amount)}
        </td>
        <td><span class="badge ${badgeClass}">${p.status}</span></td>
        <td>
          ${p.allocations && p.allocations.length > 0 ? `
            <button class="btn btn-secondary btn-sm" onclick="viewAllocations(${p.id})">
              🔗 ${p.allocations.length} Linked
            </button>
          ` : '<span style="color:var(--text-muted); font-size:0.8rem">No links</span>'}
        </td>
      </tr>
    `;
  }).join('');
}

function renderChequesTable(cheques) {
  const tbody = document.getElementById('cheques-tbody');
  if (!tbody) return;

  if (cheques.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:32px; color:var(--text-muted)">No Post-Dated Cheques in registry.</td></tr>`;
    return;
  }

  tbody.innerHTML = cheques.map(chq => {
    let badgeClass = 'badge-issued';
    if (chq.status === 'Cleared') badgeClass = 'badge-paid';
    else if (chq.status === 'Bounced') badgeClass = 'badge-overdue';

    return `
      <tr>
        <td style="font-weight:700; color:var(--primary); font-family:monospace;">${chq.cheque_number}</td>
        <td style="font-weight:600">${chq.customer_name}</td>
        <td>${chq.bank_name}</td>
        <td>${formatDate(chq.issue_date)}</td>
        <td style="font-weight:600; color:var(--secondary)">${formatDate(chq.maturity_date)}</td>
        <td class="amount" style="font-weight:800">${formatPKR(chq.amount)}</td>
        <td><span class="badge ${badgeClass}">${chq.status}</span></td>
        <td>
          ${chq.status === 'Pending Deposit' ? `
            <div style="display:flex; gap:6px;">
              <button class="btn btn-accent btn-sm" onclick="changeChequeStatus(${chq.id}, 'Cleared')">
                ✓ Clear Cheque
              </button>
              <button class="btn btn-danger btn-sm" onclick="changeChequeStatus(${chq.id}, 'Bounced')">
                ✕ Bounce
              </button>
            </div>
          ` : `<span style="font-size:0.8rem; color:var(--text-muted)">Archived (${chq.status})</span>`}
        </td>
      </tr>
    `;
  }).join('');
}

async function changeChequeStatus(chequeId, newStatus) {
  const confirmMsg = newStatus === 'Cleared' 
    ? 'Are you sure you want to mark this cheque as CLEARED? This will automatically credit the customer account and auto-reconcile open invoices.'
    : 'Mark this cheque as BOUNCED?';

  if (!confirm(confirmMsg)) return;

  try {
    const res = await Api.put(`/cheques/${chequeId}/status`, { status: newStatus });
    showToast(`Cheque #${res.cheque_number} marked as ${newStatus}`, 'success');
    loadCheques();
    if (newStatus === 'Cleared') loadPayments();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Record Payment Submit
async function handleRecordPayment(e) {
  e.preventDefault();
  const customerId = parseInt(document.getElementById('payment-customer-select').value);
  if (!customerId) {
    showToast('Please select a customer account.', 'warning');
    return;
  }

  const amount = parseFloat(document.getElementById('payment-amount').value);
  if (!amount || amount <= 0) {
    showToast('Please enter a valid payment amount.', 'warning');
    return;
  }

  const paymentDate = document.getElementById('payment-date').value;
  const paymentMethod = document.getElementById('payment-method').value;
  const refNo = document.getElementById('payment-reference').value.trim() || null;
  const bankName = document.getElementById('payment-bank').value.trim() || null;
  const notes = document.getElementById('payment-notes').value.trim() || null;
  const autoAllocate = document.getElementById('payment-auto-fifo').checked;

  const payload = {
    customer_id: customerId,
    amount: amount,
    payment_date: paymentDate,
    payment_method: paymentMethod,
    reference_number: refNo,
    bank_name: bankName,
    notes: notes,
    auto_allocate_fifo: autoAllocate
  };

  try {
    const res = await Api.post('/payments', payload);
    showToast(`Payment ${res.payment_number} recorded successfully!`, 'success');
    closeModal('modal-record-payment');
    document.getElementById('form-record-payment').reset();
    loadPayments();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Record Cheque Submit
async function handleRecordCheque(e) {
  e.preventDefault();
  const customerId = parseInt(document.getElementById('cheque-customer-select').value);
  if (!customerId) {
    showToast('Please select a customer account.', 'warning');
    return;
  }

  const payload = {
    customer_id: customerId,
    cheque_number: document.getElementById('cheque-num').value.trim(),
    bank_name: document.getElementById('cheque-bank').value.trim(),
    amount: parseFloat(document.getElementById('cheque-amount').value) || 0,
    issue_date: document.getElementById('cheque-issue-date').value,
    maturity_date: document.getElementById('cheque-maturity-date').value,
    notes: document.getElementById('cheque-notes').value.trim() || null
  };

  if (!payload.cheque_number || payload.amount <= 0) {
    showToast('Please enter valid cheque number and amount.', 'warning');
    return;
  }

  try {
    const res = await Api.post('/cheques', payload);
    showToast(`Post-Dated Cheque #${res.cheque_number} recorded!`, 'success');
    closeModal('modal-record-cheque');
    document.getElementById('form-record-cheque').reset();
    switchPaymentTab('cheques');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// View Payment Allocations Modal
function viewAllocations(paymentId) {
  const payment = allPayments.find(p => p.id === paymentId);
  if (!payment) return;

  const tbody = document.getElementById('allocations-modal-tbody');
  document.getElementById('alloc-payment-num').textContent = payment.payment_number;
  document.getElementById('alloc-payment-total').textContent = formatPKR(payment.amount);
  document.getElementById('alloc-payment-unallocated').textContent = formatPKR(payment.unallocated_amount);

  tbody.innerHTML = payment.allocations.map(a => `
    <tr>
      <td style="font-weight:600; color:var(--primary)">${a.invoice_number}</td>
      <td class="amount" style="color:var(--accent); font-weight:700">${formatPKR(a.allocated_amount)}</td>
      <td>${formatDate(a.allocated_at)}</td>
      <td style="font-size:0.85rem; color:var(--text-muted)">${a.notes || 'Auto-Allocated'}</td>
    </tr>
  `).join('');

  openModal('modal-view-allocations');
}

document.addEventListener('DOMContentLoaded', () => {
  loadPayments();
  loadCustomersDropdown();

  const today = new Date().toISOString().split('T')[0];
  const dateEl = document.getElementById('payment-date');
  const chqIssueEl = document.getElementById('cheque-issue-date');
  const chqMatEl = document.getElementById('cheque-maturity-date');

  if (dateEl) dateEl.value = today;
  if (chqIssueEl) chqIssueEl.value = today;
  if (chqMatEl) chqMatEl.value = new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0];

  const searchInput = document.getElementById('search-payment');
  if (searchInput) searchInput.addEventListener('input', () => loadPayments());

  const statusFilter = document.getElementById('filter-status');
  if (statusFilter) statusFilter.addEventListener('change', () => loadPayments());

  const formPay = document.getElementById('form-record-payment');
  if (formPay) formPay.addEventListener('submit', handleRecordPayment);

  const formChq = document.getElementById('form-record-cheque');
  if (formChq) formChq.addEventListener('submit', handleRecordCheque);
});
