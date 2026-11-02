// State
let selectedFile = null;
let allTransactions = [];
let currentFilter = 'ALL';
let verifyMode = 'simulate'; // 'simulate' or 'reconcile'
let lastInspectedData = null;
let currentTab = 'dashboard';

// Format COP currency
function formatCOP(amount) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0
  }).format(amount || 0);
}

// Switch between Navigation Tabs (Dashboard, Ingresos, Escanear)
function switchTab(tab) {
  currentTab = tab;
  const tabs = ['dashboard', 'ingresos', 'escanear'];
  const titles = {
    'dashboard': 'Dashboard General',
    'ingresos': 'Ingresos y Conciliaciones',
    'escanear': 'Subir Comprobante / QR Bancario'
  };

  tabs.forEach(t => {
    const view = document.getElementById(`view-${t}`);
    const navBtn = document.getElementById(`nav-${t}`);
    if (view && navBtn) {
      if (t === tab) {
        view.classList.add('active');
        navBtn.className = "w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold transition bg-blue-50 text-blue-700";
        // make sure icon is blue
        const icon = navBtn.querySelector('i');
        if (icon) icon.className = "w-4 h-4 text-blue-600";
      } else {
        view.classList.remove('active');
        navBtn.className = "w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition";
        const icon = navBtn.querySelector('i');
        if (icon && t === 'ingresos') icon.className = "w-4 h-4 text-emerald-600";
        else if (icon) icon.className = "w-4 h-4 text-slate-500";
      }
    }
  });

  const pageTitle = document.getElementById('page-title');
  if (pageTitle && titles[tab]) {
    pageTitle.textContent = titles[tab];
  }

  if (tab === 'escanear' && verifyMode === 'reconcile') {
    loadPendingOrders();
  }

  lucide.createIcons();
}

// Set Verify Mode: Simulate vs Reconcile
function setVerifyMode(mode) {
  verifyMode = mode;
  const simBtn = document.getElementById('mode-simulate-btn');
  const orderBtn = document.getElementById('mode-order-btn');
  const orderContainer = document.getElementById('order-select-container');
  const submitBtn = document.getElementById('submit-verify-btn');

  if (mode === 'simulate') {
    simBtn.className = "flex-1 py-2 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center space-x-1.5 bg-blue-600 text-white shadow-xs";
    orderBtn.className = "flex-1 py-2 px-3 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition flex items-center justify-center space-x-1.5";
    orderContainer.classList.add('hidden');
    document.getElementById('order-select').required = false;
    submitBtn.innerHTML = '<i data-lucide="flask-conical" class="w-4 h-4"></i><span>Inspeccionar y Extraer Datos</span>';
  } else {
    orderBtn.className = "flex-1 py-2 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center space-x-1.5 bg-blue-600 text-white shadow-xs";
    simBtn.className = "flex-1 py-2 px-3 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition flex items-center justify-center space-x-1.5";
    orderContainer.classList.remove('hidden');
    document.getElementById('order-select').required = true;
    submitBtn.innerHTML = '<i data-lucide="shield-check" class="w-4 h-4"></i><span>Procesar y Conciliar con Orden</span>';
    loadPendingOrders();
  }
  lucide.createIcons();
}

// Load Pending Orders for Select Dropdown
async function loadPendingOrders(preselectedId = null) {
  const select = document.getElementById('order-select');
  try {
    const res = await fetch('/api/v1/orders?status_filter=PENDING');
    if (!res.ok) throw new Error('Error al cargar órdenes');
    const orders = await res.json();

    select.innerHTML = '<option value="" disabled selected>Selecciona una orden pendiente...</option>';
    
    if (orders.length === 0) {
      select.innerHTML += '<option value="" disabled>⚠️ No hay órdenes pendientes (Crea una)</option>';
    } else {
      orders.forEach(order => {
        const opt = document.createElement('option');
        opt.value = order.id;
        opt.textContent = `${order.order_number} — Total: ${formatCOP(order.total_amount)}`;
        if (preselectedId && order.id === preselectedId) {
          opt.selected = true;
        }
        select.appendChild(opt);
      });
    }
  } catch (err) {
    console.error('Error fetching orders:', err);
  }
}

// Drag & Drop Handlers
function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.add('border-blue-500', 'bg-blue-50/40');
}

function handleDragLeave(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.remove('border-blue-500', 'bg-blue-50/40');
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.remove('border-blue-500', 'bg-blue-50/40');
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    setFile(e.dataTransfer.files[0]);
  }
}

function handleFileSelected(e) {
  if (e.target.files && e.target.files[0]) {
    setFile(e.target.files[0]);
  }
}

function setFile(file) {
  if (!file.type.startsWith('image/')) {
    alert('Por favor selecciona una imagen válida (PNG, JPG, WEBP).');
    return;
  }
  selectedFile = file;

  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById('preview-img').src = e.target.result;
    document.getElementById('preview-filename').textContent = file.name;
    document.getElementById('preview-filesize').textContent = (file.size / 1024).toFixed(1) + ' KB';
    document.getElementById('dropzone-empty').classList.add('hidden');
    document.getElementById('dropzone-preview').classList.remove('hidden');
    lucide.createIcons();
  };
  reader.readAsDataURL(file);
}

function clearFileSelection(e) {
  if (e) e.stopPropagation();
  selectedFile = null;
  document.getElementById('file-input').value = '';
  document.getElementById('dropzone-empty').classList.remove('hidden');
  document.getElementById('dropzone-preview').classList.add('hidden');
}

// Handle Form Submit
async function handleVerifySubmit(e) {
  e.preventDefault();
  if (!selectedFile) {
    alert('Por favor adjunta la imagen del comprobante de pago.');
    return;
  }

  const orderId = document.getElementById('order-select').value;
  if (verifyMode === 'reconcile' && !orderId) {
    alert('Por favor selecciona una orden de venta o cambia al "Modo Simulación Libre".');
    return;
  }

  // Set Loading UI
  document.getElementById('verdict-idle').classList.add('hidden');
  document.getElementById('verdict-success').classList.add('hidden');
  document.getElementById('verdict-error').classList.add('hidden');
  document.getElementById('verdict-loading').classList.remove('hidden');
  document.getElementById('verdict-status-pill').className = "text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200";
  document.getElementById('verdict-status-pill').textContent = "Procesando...";

  const submitBtn = document.getElementById('submit-verify-btn');
  submitBtn.disabled = true;
  submitBtn.classList.add('opacity-50');

  const formData = new FormData();
  formData.append('file', selectedFile);

  try {
    let endpoint = '/api/v1/receipts/inspect';
    if (verifyMode === 'reconcile') {
      endpoint = '/api/v1/receipts/verify';
      formData.append('order_id', orderId);
    }

    const res = await fetch(endpoint, {
      method: 'POST',
      body: formData,
    });

    const data = await res.json();
    document.getElementById('verdict-loading').classList.add('hidden');

    if (res.ok) {
      lastInspectedData = data;
      document.getElementById('verdict-success').classList.remove('hidden');

      if (verifyMode === 'simulate') {
        if (data.is_duplicate) {
          document.getElementById('verdict-status-pill').className = "text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200";
          document.getElementById('verdict-status-pill').textContent = "DUPLICADO DETECTADO";
        } else {
          document.getElementById('verdict-status-pill').className = "text-[11px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200";
          document.getElementById('verdict-status-pill').textContent = "SIMULACIÓN EXITOSA";
        }

        document.getElementById('res-bank').textContent = data.bank_platform;
        document.getElementById('res-ref').textContent = data.reference_number;
        document.getElementById('res-amount').textContent = formatCOP(data.amount_cop);
        document.getElementById('res-date').textContent = new Date(data.receipt_timestamp).toLocaleString('es-CO');
        document.getElementById('res-hash').textContent = data.image_sha256;
        document.getElementById('res-hash').title = data.image_sha256;

        // Auto Reconcile CTA button
        const container = document.getElementById('verdict-success');
        let autoBtn = document.getElementById('auto-reconcile-btn');
        if (!autoBtn) {
          autoBtn = document.createElement('button');
          autoBtn.id = 'auto-reconcile-btn';
          autoBtn.className = "w-full mt-3 py-2 px-3 rounded-lg text-xs font-bold bg-slate-900 hover:bg-slate-800 text-white transition flex items-center justify-center space-x-1.5";
          autoBtn.onclick = autoReconcileInspected;
          container.appendChild(autoBtn);
        }
        autoBtn.innerHTML = `<i data-lucide="zap" class="w-3.5 h-3.5 text-amber-400"></i><span>Crear Orden de ${formatCOP(data.amount_cop)} y Conciliar</span>`;
      } else {
        document.getElementById('verdict-status-pill').className = "text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200";
        document.getElementById('verdict-status-pill').textContent = "PAGO CONCILIADO";

        document.getElementById('res-bank').textContent = data.bank_platform;
        document.getElementById('res-ref').textContent = data.reference_number;
        document.getElementById('res-amount').textContent = formatCOP(data.extracted_amount);
        document.getElementById('res-date').textContent = new Date(data.receipt_timestamp).toLocaleString('es-CO');
        document.getElementById('res-hash').textContent = data.image_sha256;
        document.getElementById('res-hash').title = data.image_sha256;

        const autoBtn = document.getElementById('auto-reconcile-btn');
        if (autoBtn) autoBtn.remove();
        loadPendingOrders();
      }

      // Refresh stats and tables
      loadAllData();
    } else {
      document.getElementById('verdict-error').classList.remove('hidden');
      document.getElementById('verdict-status-pill').className = "text-[11px] font-bold px-2 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-200";
      document.getElementById('verdict-status-pill').textContent = "RECHAZADO";

      const err = data.error || {};
      document.getElementById('error-title').textContent = err.code || 'Error en Verificación';
      document.getElementById('error-desc').textContent = err.message || 'El comprobante no pudo ser validado.';
      document.getElementById('error-details').textContent = JSON.stringify(err.details || {}, null, 2);
    }
  } catch (err) {
    document.getElementById('verdict-loading').classList.add('hidden');
    document.getElementById('verdict-error').classList.remove('hidden');
    document.getElementById('error-title').textContent = 'Error de Conexión';
    document.getElementById('error-desc').textContent = 'No se pudo comunicar con el servidor backend.';
    document.getElementById('error-details').textContent = err.message;
  } finally {
    submitBtn.disabled = false;
    submitBtn.classList.remove('opacity-50');
    lucide.createIcons();
  }
}

// Auto-Reconcile Inspected Receipt
async function autoReconcileInspected() {
  if (!lastInspectedData || !selectedFile) return;

  try {
    const orderNumber = 'ORD-' + Math.floor(1000 + Math.random() * 9000);
    const resOrder = await fetch('/api/v1/orders/quick', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        order_number: orderNumber,
        total_amount: lastInspectedData.amount_cop,
      }),
    });

    if (!resOrder.ok) throw new Error('No se pudo crear la orden automática');
    const order = await resOrder.json();

    setVerifyMode('reconcile');
    await loadPendingOrders(order.id);
    document.getElementById('order-select').value = order.id;

    const form = document.getElementById('verify-form');
    form.dispatchEvent(new Event('submit', { cancelable: true }));
  } catch (err) {
    alert('Error al auto-conciliar: ' + err.message);
  }
}

// Quick Order Modal
function openQuickOrderModal() {
  document.getElementById('quick-order-modal').classList.remove('hidden');
  document.getElementById('quick-order-number').value = 'ORD-' + Math.floor(1000 + Math.random() * 9000);
  document.getElementById('quick-order-amount').value = '';
}

function closeQuickOrderModal() {
  document.getElementById('quick-order-modal').classList.add('hidden');
}

async function handleQuickOrderSubmit(e) {
  e.preventDefault();
  const orderNumber = document.getElementById('quick-order-number').value.trim();
  const amount = parseInt(document.getElementById('quick-order-amount').value, 10);

  try {
    const res = await fetch('/api/v1/orders/quick', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_number: orderNumber, total_amount: amount }),
    });

    if (!res.ok) {
      const err = await res.json();
      alert('Error: ' + (err.detail || 'No se pudo crear la orden'));
      return;
    }

    const order = await res.json();
    closeQuickOrderModal();
    setVerifyMode('reconcile');
    await loadPendingOrders(order.id);
  } catch (err) {
    alert('Error de conexión: ' + err.message);
  }
}

// Load All Data & Update Dashboard KPIs
async function loadAllData() {
  try {
    const res = await fetch('/api/v1/receipts?limit=100');
    if (!res.ok) throw new Error('Error al consultar recibos');
    allTransactions = await res.json();

    // 1. Update KPIs
    updateKPIs(allTransactions);

    // 2. Render Recent Dashboard Table
    renderDashboardRecent(allTransactions.slice(0, 5));

    // 3. Render Ingresos Table
    renderIngresosTable(allTransactions);

    // 4. Update Badge Count
    const badge = document.getElementById('badge-ingresos-count');
    if (badge) badge.textContent = allTransactions.length;

  } catch (err) {
    console.error('Error fetching data:', err);
  }
}

// Calculate and populate Forttu-style KPIs
function updateKPIs(transactions) {
  let verifiedSum = 0;
  let verifiedCount = 0;
  let simulatedSum = 0;
  let simulatedCount = 0;

  transactions.forEach(tx => {
    const amt = tx.extracted_amount || 0;
    if (tx.verification_status === 'VERIFIED') {
      verifiedSum += amt;
      verifiedCount++;
    } else if (tx.verification_status === 'SIMULATED') {
      simulatedSum += amt;
      simulatedCount++;
    }
  });

  const totalSum = verifiedSum;
  const avgTicket = verifiedCount > 0 ? Math.round(verifiedSum / verifiedCount) : 0;

  document.getElementById('stat-total-cop').textContent = formatCOP(totalSum);
  document.getElementById('stat-total-count').textContent = `${verifiedCount} comprobantes verificados`;

  document.getElementById('stat-avg-ticket').textContent = formatCOP(avgTicket);

  document.getElementById('stat-verified-count').textContent = verifiedCount;
  document.getElementById('stat-verified-sum').textContent = `${formatCOP(verifiedSum)} conciliados`;

  document.getElementById('stat-simulated-count').textContent = simulatedCount;
  document.getElementById('stat-simulated-sum').textContent = `${formatCOP(simulatedSum)} en auditoría`;
}

// Render Recent table on Dashboard
function renderDashboardRecent(list) {
  const tbody = document.getElementById('dashboard-recent-tbody');
  tbody.innerHTML = '';

  if (!list || list.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="px-5 py-6 text-center text-slate-400">Sin movimientos recientes</td></tr>';
    return;
  }

  list.forEach(tx => {
    const tr = document.createElement('tr');
    tr.className = "hover:bg-slate-50 transition";

    const dateStr = new Date(tx.created_at).toLocaleString('es-CO', {
      day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
    });

    const statusBadge = getStatusBadge(tx.verification_status);
    const bankBadge = getBankBadge(tx.bank_platform);

    tr.innerHTML = `
      <td class="px-5 py-3 font-mono text-slate-500">${dateStr}</td>
      <td class="px-5 py-3">${bankBadge}</td>
      <td class="px-5 py-3 font-mono font-bold text-slate-800">${tx.reference_number || 'N/A'}</td>
      <td class="px-5 py-3 font-bold text-slate-900">${formatCOP(tx.extracted_amount)}</td>
      <td class="px-5 py-3">${statusBadge}</td>
      <td class="px-5 py-3 text-right">
        <button onclick="openDetailModal('${tx.id}', '${tx.image_sha256}', '${tx.failure_reason || ''}')" class="text-blue-600 hover:text-blue-800 font-semibold text-[11px]">
          Detalle
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  lucide.createIcons();
}

// Render Full Ingresos Table
function renderIngresosTable(list) {
  const tbody = document.getElementById('ingresos-tbody');
  const emptyState = document.getElementById('ingresos-empty');
  tbody.innerHTML = '';

  if (!list || list.length === 0) {
    emptyState.classList.remove('hidden');
    return;
  }
  emptyState.classList.add('hidden');

  list.forEach(tx => {
    const tr = document.createElement('tr');
    tr.className = "hover:bg-slate-50 transition";

    const dateStr = new Date(tx.created_at).toLocaleString('es-CO', {
      day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });

    const bankBadge = getBankBadge(tx.bank_platform);
    const statusBadge = getStatusBadge(tx.verification_status);

    const desc = tx.failure_reason || (tx.order_id ? `Orden: ${tx.order_id.slice(0, 8)}...` : 'Inspección de mostrador');

    tr.innerHTML = `
      <td class="px-5 py-3.5 font-mono text-slate-500 whitespace-nowrap">${dateStr}</td>
      <td class="px-5 py-3.5">${bankBadge}</td>
      <td class="px-5 py-3.5 font-mono font-bold text-slate-800">${tx.reference_number || 'N/A'}</td>
      <td class="px-5 py-3.5 font-bold text-slate-900">${formatCOP(tx.extracted_amount)}</td>
      <td class="px-5 py-3.5">${statusBadge}</td>
      <td class="px-5 py-3.5 text-slate-500 truncate max-w-[200px]" title="${desc}">${desc}</td>
      <td class="px-5 py-3.5 text-right">
        <button onclick="openDetailModal('${tx.id}', '${tx.image_sha256}', '${tx.failure_reason || ''}')" class="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-[11px] transition">
          Forense
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  lucide.createIcons();
}

// Helpers for badges
function getBankBadge(bank) {
  if (bank === 'NEQUI') {
    return `<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-fuchsia-100 text-fuchsia-800 border border-fuchsia-200">Nequi</span>`;
  } else if (bank === 'DAVIPLATA') {
    return `<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-red-100 text-red-800 border border-red-200">DaviPlata</span>`;
  } else if (bank === 'BANCOLOMBIA') {
    return `<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">Bancolombia</span>`;
  } else if (bank === 'BRE_B') {
    return `<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-teal-100 text-teal-800 border border-teal-200">Bre-B</span>`;
  } else if (bank === 'DIAN_INVOICE') {
    return `<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-blue-100 text-blue-800 border border-blue-200">DIAN QR</span>`;
  }
  return `<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-600">${bank || 'OTRO'}</span>`;
}

function getStatusBadge(status) {
  if (status === 'VERIFIED') {
    return `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200"><i data-lucide="check" class="w-3 h-3 mr-1"></i> Conciliado</span>`;
  } else if (status === 'SIMULATED') {
    return `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200"><i data-lucide="flask-conical" class="w-3 h-3 mr-1"></i> Simulado</span>`;
  } else if (status === 'DUPLICATE') {
    return `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200"><i data-lucide="copy" class="w-3 h-3 mr-1"></i> Duplicado</span>`;
  } else if (status === 'REJECTED') {
    return `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-red-50 text-red-700 border border-red-200"><i data-lucide="x" class="w-3 h-3 mr-1"></i> Rechazado</span>`;
  }
  return `<span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-500">${status}</span>`;
}

// Filter Ingresos Table
function setIngresosFilter(status) {
  currentFilter = status;
  ['ALL', 'VERIFIED', 'SIMULATED', 'REJECTED'].forEach(s => {
    const btn = document.getElementById(`filter-ing-${s}`);
    if (!btn) return;
    if (s === status) {
      btn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 text-white transition";
    } else {
      btn.className = "px-3 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100 transition";
    }
  });
  filterIngresos();
}

function filterIngresos() {
  const query = (document.getElementById('ingresos-search').value || '').toLowerCase().trim();
  const filtered = allTransactions.filter(tx => {
    if (currentFilter !== 'ALL' && tx.verification_status !== currentFilter) {
      return false;
    }
    if (query) {
      const matchRef = (tx.reference_number || '').toLowerCase().includes(query);
      const matchBank = (tx.bank_platform || '').toLowerCase().includes(query);
      const matchAmt = (tx.extracted_amount || '').toString().includes(query);
      return matchRef || matchBank || matchAmt;
    }
    return true;
  });
  renderIngresosTable(filtered);
}

// Forensic Modal
function openDetailModal(id, hash, reason) {
  document.getElementById('modal-id').textContent = id;
  document.getElementById('modal-hash').textContent = hash;
  
  const reasonBox = document.getElementById('modal-reason-box');
  if (reason && reason !== 'null' && reason !== '') {
    reasonBox.classList.remove('hidden');
    document.getElementById('modal-reason').textContent = reason;
  } else {
    reasonBox.classList.add('hidden');
  }
  document.getElementById('detail-modal').classList.remove('hidden');
}

function closeDetailModal() {
  document.getElementById('detail-modal').classList.add('hidden');
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
  switchTab('dashboard');
  loadAllData();
  lucide.createIcons();
});
