/**
 * Customers & Account Statement Controller
 */

let allCustomers = [];

async function loadCustomers() {
  const search = document.getElementById('search-customer')?.value || '';
  const city = document.getElementById('filter-city')?.value || '';

  try {
    const params = {};
    if (search) params.search = search;
    if (city) params.city = city;

    allCustomers = await Api.get('/customers', params);
    renderCustomersTable(allCustomers);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderCustomersTable(customers) {
  const tbody = document.getElementById('customers-tbody');
  if (!tbody) return;

  if (customers.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:32px; color:var(--text-muted)">No customer accounts found matching your criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = customers.map(c => `
    <tr>
      <td>
        <div style="font-weight:600; color:var(--secondary)">${c.name}</div>
        <div style="font-size:0.75rem; color:var(--text-muted)">${c.company_name || '-'}</div>
      </td>
      <td>${c.city || 'City'}</td>
      <td>${c.phone}</td>
      <td class="amount">${formatPKR(c.credit_limit)}</td>
      <td class="amount" style="color: ${c.current_balance > 0 ? 'var(--danger)' : 'var(--accent)'}; font-weight:700">
        ${formatPKR(c.current_balance)}
      </td>
      <td>
        <span class="badge ${c.is_active ? 'badge-paid' : 'badge-cancelled'}">
          ${c.is_active ? 'Active' : 'Inactive'}
        </span>
      </td>
      <td>
        <div style="display:flex; gap:6px;">
          <button class="btn btn-secondary btn-sm" onclick="viewCustomerLedger(${c.id})">
            📄 Statement
          </button>
        </div>
      </td>
    </tr>
  `).join('');
}

// Add Customer Handler
async function handleAddCustomer(e) {
  e.preventDefault();
  const form = e.target;

  const data = {
    name: form.name.value.trim(),
    company_name: form.company_name.value.trim(),
    phone: form.phone.value.trim(),
    email: form.email.value.trim() || null,
    city: form.city.value.trim() || 'Lahore',
    address: form.address.value.trim() || null,
    ntn_number: form.ntn_number.value.trim() || null,
    credit_limit: parseFloat(form.credit_limit.value) || 100000,
    payment_terms_days: parseInt(form.payment_terms_days.value) || 15
  };

  try {
    const res = await Api.post('/customers', data);
    showToast(`Account '${res.name}' created successfully!`, 'success');
    closeModal('modal-add-customer');
    form.reset();
    loadCustomers();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// View Customer Statement of Account
async function viewCustomerLedger(customerId) {
  try {
    const data = await Api.get(`/customers/${customerId}/ledger`);
    const modal = document.getElementById('modal-customer-ledger');
    if (!modal) return;

    document.getElementById('ledger-customer-name').textContent = data.customer.name;
    document.getElementById('ledger-customer-company').textContent = data.customer.company_name;
    document.getElementById('ledger-total-invoiced').textContent = formatPKR(data.summary.total_invoiced);
    document.getElementById('ledger-total-paid').textContent = formatPKR(data.summary.total_paid);
    document.getElementById('ledger-net-balance').textContent = formatPKR(data.summary.net_outstanding);

    const tbody = document.getElementById('ledger-statement-tbody');
    if (!data.statement || data.statement.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:24px; color:var(--text-muted)">No transactions recorded for this account yet.</td></tr>`;
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

    // Set export link
    const exportBtn = document.getElementById('btn-export-ledger');
    if (exportBtn) {
      exportBtn.onclick = () => {
        window.open(`/api/reports/export/ledger?customer_id=${customerId}`, '_blank');
      };
    }

    // Set WhatsApp statement link
    const whatsappBtn = document.getElementById('btn-whatsapp-statement');
    if (whatsappBtn) {
      whatsappBtn.onclick = () => {
        const rawPhone = data.customer.phone || '';
        let cleanPhone = rawPhone.replace(/\D/g, '');
        if (cleanPhone.startsWith('0')) cleanPhone = '92' + cleanPhone.substring(1);
        const msg = `Dear ${data.customer.name},\n\nPlease find your updated Statement of Account with ${Api.getBusinessName()}:\n• Total Invoiced: ${formatPKR(data.summary.total_invoiced)}\n• Payments Received: ${formatPKR(data.summary.total_paid)}\n• Current Outstanding Balance: ${formatPKR(data.summary.net_outstanding)}\n\nPlease remit outstanding balance via Raast / Bank Wire.\nThank you!`;
        const url = `https://api.whatsapp.com/send?phone=${cleanPhone}&text=${encodeURIComponent(msg)}`;
        window.open(url, '_blank');
      };
    }

    openModal('modal-customer-ledger');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadCustomers();

  const searchInput = document.getElementById('search-customer');
  if (searchInput) {
    searchInput.addEventListener('input', () => loadCustomers());
  }

  const cityFilter = document.getElementById('filter-city');
  if (cityFilter) {
    cityFilter.addEventListener('change', () => loadCustomers());
  }

  const addForm = document.getElementById('form-add-customer');
  if (addForm) {
    addForm.addEventListener('submit', handleAddCustomer);
  }
});
