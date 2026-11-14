/**
 * Inventory & Stock Controller
 */

let allProducts = [];

async function loadProducts() {
  const search = document.getElementById('search-product')?.value || '';
  const lowStock = document.getElementById('filter-low-stock')?.checked || false;

  try {
    const params = {};
    if (search) params.search = search;
    if (lowStock) params.low_stock_only = true;

    allProducts = await Api.get('/products', params);
    renderProductsTable(allProducts);
    updateInventoryKPIs(allProducts);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function updateInventoryKPIs(products) {
  const totalSkus = products.length;
  let totalValuation = 0;
  let lowStockCount = 0;

  products.forEach(p => {
    totalValuation += (p.stock_quantity * p.unit_price);
    if (p.stock_quantity <= p.reorder_level) {
      lowStockCount++;
    }
  });

  const skuEl = document.getElementById('kpi-total-skus');
  const valEl = document.getElementById('kpi-total-valuation');
  const lowEl = document.getElementById('kpi-low-stock-count');

  if (skuEl) skuEl.textContent = totalSkus;
  if (valEl) valEl.textContent = formatPKR(totalValuation);
  if (lowEl) lowEl.textContent = lowStockCount;
}

function renderProductsTable(products) {
  const tbody = document.getElementById('products-tbody');
  if (!tbody) return;

  if (products.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:32px; color:var(--text-muted)">No inventory items found.</td></tr>`;
    return;
  }

  tbody.innerHTML = products.map(p => {
    const isLow = p.stock_quantity <= p.reorder_level;
    const assetVal = roundNum(p.stock_quantity * p.unit_price);

    return `
      <tr>
        <td style="font-weight:700; color:var(--primary); font-family:monospace;">${p.sku}</td>
        <td>
          <div style="font-weight:600; color:var(--secondary)">${p.name}</div>
        </td>
        <td>${p.category || 'General'}</td>
        <td class="amount">${formatPKR(p.unit_cost)}</td>
        <td class="amount" style="font-weight:600">${formatPKR(p.unit_price)}</td>
        <td class="amount" style="font-weight:800; color:${isLow ? 'var(--danger)' : 'var(--secondary)'}">
          ${p.stock_quantity} <span style="font-size:0.75rem; font-weight:normal; color:var(--text-muted)">${p.unit}s</span>
        </td>
        <td class="amount" style="font-weight:700; color:var(--accent)">${formatPKR(assetVal)}</td>
        <td>
          <span class="badge ${isLow ? 'badge-overdue' : 'badge-paid'}">
            ${isLow ? '⚠️ Low Stock' : 'In Stock'}
          </span>
        </td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="promptAdjustStock(${p.id}, '${p.name}', ${p.stock_quantity})">
            Adjust Qty
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function roundNum(num) {
  return Math.round(num * 100) / 100;
}

async function promptAdjustStock(productId, name, currentQty) {
  const newQtyStr = prompt(`Enter updated stock quantity for "${name}":`, currentQty);
  if (newQtyStr === null) return;
  const newQty = parseFloat(newQtyStr);
  if (isNaN(newQty) || newQty < 0) {
    showToast('Invalid stock quantity entered.', 'warning');
    return;
  }

  try {
    await Api.put(`/products/${productId}`, { stock_quantity: newQty });
    showToast(`Stock updated for ${name}`, 'success');
    loadProducts();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function handleAddProduct(e) {
  e.preventDefault();
  const form = e.target;

  const data = {
    sku: document.getElementById('prod-sku').value.trim(),
    name: document.getElementById('prod-name').value.trim(),
    category: document.getElementById('prod-category').value.trim() || 'General',
    unit: document.getElementById('prod-unit').value.trim() || 'Carton',
    stock_quantity: parseFloat(document.getElementById('prod-stock').value) || 0,
    unit_cost: parseFloat(document.getElementById('prod-cost').value) || 0,
    unit_price: parseFloat(document.getElementById('prod-price').value) || 0,
    reorder_level: parseFloat(document.getElementById('prod-reorder').value) || 10
  };

  try {
    const res = await Api.post('/products', data);
    showToast(`Product SKU '${res.sku}' created successfully!`, 'success');
    closeModal('modal-add-product');
    form.reset();
    loadProducts();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadProducts();

  const searchInput = document.getElementById('search-product');
  if (searchInput) {
    searchInput.addEventListener('input', () => loadProducts());
  }

  const lowStockFilter = document.getElementById('filter-low-stock');
  if (lowStockFilter) {
    lowStockFilter.addEventListener('change', () => loadProducts());
  }

  const form = document.getElementById('form-add-product');
  if (form) {
    form.addEventListener('submit', handleAddProduct);
  }
});
