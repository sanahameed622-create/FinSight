/**
 * Invoices Management Controller
 */

let allInvoices = [];
let availableCustomers = [];

async function loadInvoices() {
  const search = document.getElementById('search-invoice')?.value || '';
  const status = document.getElementById('filter-status')?.value || '';

  try {
    const params = {};
    if (search) params.search = search;
    if (status && status !== 'All') params.status = status;

    allInvoices = await Api.get('/invoices', params);
    renderInvoicesTable(allInvoices);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadCustomersDropdown() {
  try {
    availableCustomers = await Api.get('/customers');
    const select = document.getElementById('invoice-customer-select');
    if (select) {
      select.innerHTML = '<option value="">-- Select Customer Account --</option>' +
        availableCustomers.map(c => `<option value="${c.id}">${c.name} (${c.city || 'City'})</option>`).join('');
    }
  } catch (err) {
    console.error('Error loading customers for dropdown:', err);
  }
}

function renderInvoicesTable(invoices) {
  const tbody = document.getElementById('invoices-tbody');
  if (!tbody) return;

  if (invoices.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:32px; color:var(--text-muted)">No invoices found matching your filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = invoices.map(inv => {
    let badgeClass = 'badge-issued';
    if (inv.status === 'Paid') badgeClass = 'badge-paid';
    else if (inv.status === 'Partially Paid') badgeClass = 'badge-partially-paid';
    else if (inv.status === 'Overdue') badgeClass = 'badge-overdue';
    else if (inv.status === 'Cancelled') badgeClass = 'badge-cancelled';

    return `
      <tr>
        <td style="font-weight:700; color:var(--primary)">${inv.invoice_number}</td>
        <td>${inv.customer_name}</td>
        <td>${formatDate(inv.issue_date)}</td>
        <td>${formatDate(inv.due_date)}</td>
        <td class="amount">${formatPKR(inv.total_amount)}</td>
        <td class="amount" style="color:var(--accent)">${formatPKR(inv.paid_amount)}</td>
        <td class="amount" style="color: ${inv.balance_due > 0 ? 'var(--danger)' : 'var(--accent)'}; font-weight:700">
          ${formatPKR(inv.balance_due)}
        </td>
        <td><span class="badge ${badgeClass}">${inv.status}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="viewInvoiceDetail(${inv.id})">
            👁️ View & Print
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

// Line Items Dynamic Table
function addInvoiceLineItem(desc = '', qty = 1, price = 0) {
  const tbody = document.getElementById('invoice-items-tbody');
  if (!tbody) return;

  const row = document.createElement('tr');
  row.className = 'line-item-row';
  row.innerHTML = `
    <td>
      <input type="text" class="item-desc form-control" placeholder="e.g. Dalda Cooking Oil 5L (Carton of 4)" value="${desc}" required />
    </td>
    <td style="width: 100px;">
      <input type="number" class="item-qty form-control" min="1" step="any" value="${qty}" oninput="recalcInvoiceTotals()" required />
    </td>
    <td style="width: 140px;">
      <input type="number" class="item-price form-control" min="0" step="any" value="${price}" oninput="recalcInvoiceTotals()" required />
    </td>
    <td style="width: 140px; text-align: right; font-weight:600;" class="item-total">
      Rs. 0
    </td>
    <td style="width: 50px; text-align: center;">
      <button type="button" class="btn-remove-row" onclick="removeLineItem(this)">✕</button>
    </td>
  `;
  tbody.appendChild(row);
  recalcInvoiceTotals();
}

function removeLineItem(btn) {
  const row = btn.closest('tr');
  const tbody = document.getElementById('invoice-items-tbody');
  if (tbody.querySelectorAll('tr').length > 1) {
    row.remove();
    recalcInvoiceTotals();
  } else {
    showToast('Invoice must have at least one line item.', 'warning');
  }
}

function recalcInvoiceTotals() {
  const rows = document.querySelectorAll('.line-item-row');
  let subtotal = 0;

  rows.forEach(r => {
    const qty = parseFloat(r.querySelector('.item-qty').value) || 0;
    const price = parseFloat(r.querySelector('.item-price').value) || 0;
    const lineTotal = roundNum(qty * price);
    r.querySelector('.item-total').textContent = formatPKR(lineTotal);
    subtotal += lineTotal;
  });

  const tax = parseFloat(document.getElementById('invoice-tax')?.value) || 0;
  const discount = parseFloat(document.getElementById('invoice-discount')?.value) || 0;
  const grandTotal = Math.max(0, subtotal + tax - discount);

  if (document.getElementById('inv-subtotal-disp')) {
    document.getElementById('inv-subtotal-disp').textContent = formatPKR(subtotal);
    document.getElementById('inv-tax-disp').textContent = formatPKR(tax);
    document.getElementById('inv-discount-disp').textContent = formatPKR(discount);
    document.getElementById('inv-total-disp').textContent = formatPKR(grandTotal);
  }
}

function roundNum(num) {
  return Math.round(num * 100) / 100;
}

// View & Print Invoice Detail Modal
async function viewInvoiceDetail(invoiceId) {
  try {
    const inv = await Api.get(`/invoices/${invoiceId}`);

    document.getElementById('view-inv-num').textContent = inv.invoice_number;
    document.getElementById('view-inv-customer').textContent = inv.customer_name;
    document.getElementById('view-inv-date').textContent = formatDate(inv.issue_date);
    document.getElementById('view-inv-due').textContent = formatDate(inv.due_date);
    document.getElementById('view-inv-status').textContent = inv.status;

    document.getElementById('view-inv-subtotal').textContent = formatPKR(inv.subtotal);
    document.getElementById('view-inv-tax').textContent = formatPKR(inv.tax_amount);
    document.getElementById('view-inv-discount').textContent = formatPKR(inv.discount_amount);
    document.getElementById('view-inv-total').textContent = formatPKR(inv.total_amount);
    document.getElementById('view-inv-balance').textContent = formatPKR(inv.balance_due);

    const tbody = document.getElementById('view-inv-items-tbody');
    if (inv.items && inv.items.length > 0) {
      tbody.innerHTML = inv.items.map(item => `
        <tr>
          <td style="font-weight:600">${item.item_description}</td>
          <td style="text-align:right">${item.quantity}</td>
          <td class="amount">${formatPKR(item.unit_price)}</td>
          <td class="amount" style="font-weight:700">${formatPKR(item.total)}</td>
        </tr>
      `).join('');
    } else {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:12px; color:var(--text-muted)">General Consignment</td></tr>`;
    }

    // Configure WhatsApp Button
    const waBtn = document.getElementById('btn-whatsapp-invoice');
    if (waBtn) {
      waBtn.onclick = () => {
        const msg = `Dear ${inv.customer_name},\n\nPlease find your Commercial Invoice *#${inv.invoice_number}* from ${Api.getBusinessName()}:\n• Total Amount: ${formatPKR(inv.total_amount)}\n• Balance Due: ${formatPKR(inv.balance_due)}\n• Payment Due Date: ${formatDate(inv.due_date)}\n\nPlease settle via Raast / Bank Wire.\nThank you!`;
        const url = `https://api.whatsapp.com/send?text=${encodeURIComponent(msg)}`;
        window.open(url, '_blank');
      };
    }

    openModal('modal-view-invoice');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Create Invoice Submit
async function handleCreateInvoice(e) {
  e.preventDefault();
  const customerId = parseInt(document.getElementById('invoice-customer-select').value);
  if (!customerId) {
    showToast('Please select a customer account.', 'warning');
    return;
  }

  const issueDate = document.getElementById('invoice-issue-date').value;
  const dueDate = document.getElementById('invoice-due-date').value;
  const tax = parseFloat(document.getElementById('invoice-tax').value) || 0;
  const discount = parseFloat(document.getElementById('invoice-discount').value) || 0;
  const notes = document.getElementById('invoice-notes').value.trim();

  const rows = document.querySelectorAll('.line-item-row');
  const items = [];
  rows.forEach(r => {
    const desc = r.querySelector('.item-desc').value.trim();
    const qty = parseFloat(r.querySelector('.item-qty').value) || 0;
    const unitPrice = parseFloat(r.querySelector('.item-price').value) || 0;
    if (desc && qty > 0) {
      items.push({
        item_description: desc,
        quantity: qty,
        unit_price: unitPrice,
        total: roundNum(qty * unitPrice)
      });
    }
  });

  if (items.length === 0) {
    showToast('Please add at least one valid line item with quantity.', 'warning');
    return;
  }

  const payload = {
    customer_id: customerId,
    issue_date: issueDate,
    due_date: dueDate,
    tax_amount: tax,
    discount_amount: discount,
    notes: notes,
    items: items
  };

  try {
    const res = await Api.post('/invoices', payload);
    showToast(`Invoice ${res.invoice_number} issued successfully!`, 'success');
    closeModal('modal-create-invoice');
    document.getElementById('form-create-invoice').reset();
    document.getElementById('invoice-items-tbody').innerHTML = '';
    addInvoiceLineItem();
    loadInvoices();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadInvoices();
  loadCustomersDropdown();

  const today = new Date().toISOString().split('T')[0];
  const due = new Date(Date.now() + 15 * 86400000).toISOString().split('T')[0];
  const issueEl = document.getElementById('invoice-issue-date');
  const dueEl = document.getElementById('invoice-due-date');
  if (issueEl) issueEl.value = today;
  if (dueEl) dueEl.value = due;

  addInvoiceLineItem();

  const searchInput = document.getElementById('search-invoice');
  if (searchInput) searchInput.addEventListener('input', () => loadInvoices());

  const statusFilter = document.getElementById('filter-status');
  if (statusFilter) statusFilter.addEventListener('change', () => loadInvoices());

  const createForm = document.getElementById('form-create-invoice');
  if (createForm) createForm.addEventListener('submit', handleCreateInvoice);
});
