// State
let selectedFile = null;
let allTransactions = [];
let currentFilter = 'ALL';
let verifyMode = 'simulate'; // 'simulate' (default, free inspection) or 'reconcile' (requires order)
let lastInspectedData = null;

// Format COP currency
function formatCOP(amount) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0
  }).format(amount);
}

// Set Verify Mode: Simulate vs Reconcile
function setVerifyMode(mode) {
  verifyMode = mode;
  const simBtn = document.getElementById('mode-simulate-btn');
  const orderBtn = document.getElementById('mode-order-btn');
  const orderContainer = document.getElementById('order-select-container');
  const submitBtn = document.getElementById('submit-verify-btn');

  if (mode === 'simulate') {
    simBtn.className = "py-2 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center space-x-1.5 bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/20";
    orderBtn.className = "py-2 px-3 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition flex items-center justify-center space-x-1.5";
    orderContainer.classList.add('hidden');
    document.getElementById('order-select').required = false;
    submitBtn.innerHTML = '<i data-lucide="flask-conical" class="w-5 h-5"></i><span>Inspeccionar y Simular Comprobante</span>';
  } else {
    orderBtn.className = "py-2 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center space-x-1.5 bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/20";
    simBtn.className = "py-2 px-3 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition flex items-center justify-center space-x-1.5";
    orderContainer.classList.remove('hidden');
    document.getElementById('order-select').required = true;
    submitBtn.innerHTML = '<i data-lucide="shield-check" class="w-5 h-5"></i><span>Procesar y Conciliar con Orden</span>';
    loadPendingOrders();
  }
  lucide.createIcons();
}

// Switch between Navigation Tabs
function switchTab(tab) {
  const verifyTab = document.getElementById('tab-verify');
  const transTab = document.getElementById('tab-transactions');
  const btnVerify = document.getElementById('tab-btn-verify');
  const btnTrans = document.getElementById('tab-btn-transactions');

  if (tab === 'verify') {
    verifyTab.classList.remove('hidden');
    transTab.classList.add('hidden');

    btnVerify.className = "flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/20";
    btnTrans.className = "flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 transition-all";
    if (verifyMode === 'reconcile') {
      loadPendingOrders();
    }
  } else {
    verifyTab.classList.add('hidden');
    transTab.classList.remove('hidden');

    btnTrans.className = "flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all bg-emerald-500 text-slate-950 shadow-sm shadow-emerald-500/20";
    btnVerify.className = "flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 transition-all";
    loadTransactions();
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
      select.innerHTML += '<option value="" disabled>⚠️ No hay órdenes pendientes (Crea una arriba)</option>';
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
  document.getElementById('dropzone').classList.add('border-emerald-500', 'bg-slate-900/80');
}

function handleDragLeave(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.remove('border-emerald-500', 'bg-slate-900/80');
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.remove('border-emerald-500', 'bg-slate-900/80');
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

  // Show preview
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

// Submit Verification / Simulation to Backend
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

  // Set UI Loading State
  document.getElementById('verdict-idle').classList.add('hidden');
  document.getElementById('verdict-success').classList.add('hidden');
  document.getElementById('verdict-error').classList.add('hidden');
  document.getElementById('verdict-loading').classList.remove('hidden');
  document.getElementById('verdict-status-pill').className = "text-xs font-bold px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20";
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
        // Simulation Result
        if (data.is_duplicate) {
          document.getElementById('verdict-status-pill').className = "text-xs font-bold px-2.5 py-1 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30";
          document.getElementById('verdict-status-pill').textContent = "DUPLICADO DETECTADO";
        } else {
          document.getElementById('verdict-status-pill').className = "text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
          document.getElementById('verdict-status-pill').textContent = "SIMULACIÓN EXITOSA";
        }

        document.getElementById('res-bank').textContent = data.bank_platform;
        document.getElementById('res-ref').textContent = data.reference_number;
        document.getElementById('res-amount').textContent = formatCOP(data.amount_cop);
        document.getElementById('res-date').textContent = new Date(data.receipt_timestamp).toLocaleString('es-CO');
        document.getElementById('res-hash').textContent = data.image_sha256;
        document.getElementById('res-hash').title = data.image_sha256;

        // Render Quick Reconcile Button if in simulation mode
        const container = document.getElementById('verdict-success');
        let autoBtn = document.getElementById('auto-reconcile-btn');
        if (!autoBtn) {
          autoBtn = document.createElement('button');
          autoBtn.id = 'auto-reconcile-btn';
          autoBtn.className = "w-full mt-4 py-2.5 px-4 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-emerald-500/30 transition flex items-center justify-center space-x-2";
          autoBtn.onclick = autoReconcileInspected;
          container.appendChild(autoBtn);
        }
        autoBtn.innerHTML = `<i data-lucide="zap" class="w-4 h-4"></i><span>Crear Orden de ${formatCOP(data.amount_cop)} y Conciliar</span>`;
      } else {
        // Reconcile Result
        document.getElementById('verdict-status-pill').className = "text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
        document.getElementById('verdict-status-pill').textContent = "PAGO VERIFICADO";

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
    } else {
      // Error
      document.getElementById('verdict-error').classList.remove('hidden');
      document.getElementById('verdict-status-pill').className = "text-xs font-bold px-2.5 py-1 rounded-full bg-red-500/20 text-red-400 border border-red-500/30";
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
    const orderNumber = 'ORD-AUTO-' + Math.floor(1000 + Math.random() * 9000);
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

    // Now reconcile
    setVerifyMode('reconcile');
    await loadPendingOrders(order.id);
    document.getElementById('order-select').value = order.id;

    // Trigger verify
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

// Load and Render Transactions Table
async function loadTransactions() {
  const tbody = document.getElementById('transactions-tbody');
  const emptyState = document.getElementById('table-empty');
  tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-8 text-center text-slate-400">Cargando transacciones...</td></tr>';

  try {
    const res = await fetch('/api/v1/receipts?limit=100');
    if (!res.ok) throw new Error('Error al consultar historial');
    allTransactions = await res.json();

    renderTransactions(allTransactions);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="px-6 py-8 text-center text-red-400">Error al cargar historial: ${err.message}</td></tr>`;
  }
}

function renderTransactions(list) {
  const tbody = document.getElementById('transactions-tbody');
  const emptyState = document.getElementById('table-empty');
  tbody.innerHTML = '';

  if (!list || list.length === 0) {
    emptyState.classList.remove('hidden');
    return;
  }
  emptyState.classList.add('hidden');

  list.forEach(tx => {
    const tr = document.createElement('tr');
    tr.className = "hover:bg-slate-800/40 transition";

    const dateStr = new Date(tx.created_at).toLocaleString('es-CO', {
      day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });

    // Bank Badge styling
    let bankBadge = `<span class="px-2.5 py-1 rounded-md text-xs font-semibold bg-slate-800 text-slate-300">${tx.bank_platform}</span>`;
    if (tx.bank_platform === 'NEQUI') {
      bankBadge = `<span class="px-2.5 py-1 rounded-md text-xs font-semibold bg-fuchsia-950 text-fuchsia-300 border border-fuchsia-800">Nequi</span>`;
    } else if (tx.bank_platform === 'DAVIPLATA') {
      bankBadge = `<span class="px-2.5 py-1 rounded-md text-xs font-semibold bg-red-950 text-red-300 border border-red-800">DaviPlata</span>`;
    } else if (tx.bank_platform === 'BANCOLOMBIA') {
      bankBadge = `<span class="px-2.5 py-1 rounded-md text-xs font-semibold bg-yellow-950 text-yellow-300 border border-yellow-800">Bancolombia</span>`;
    } else if (tx.bank_platform === 'BRE_B') {
      bankBadge = `<span class="px-2.5 py-1 rounded-md text-xs font-semibold bg-teal-950 text-teal-300 border border-teal-800">Bre-B</span>`;
    } else if (tx.bank_platform === 'DIAN_INVOICE') {
      bankBadge = `<span class="px-2.5 py-1 rounded-md text-xs font-semibold bg-blue-950 text-blue-300 border border-blue-800">DIAN QR</span>`;
    }

    // Status Badge
    let statusBadge = `<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-400">${tx.verification_status}</span>`;
    if (tx.verification_status === 'VERIFIED') {
      statusBadge = `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><i data-lucide="check" class="w-3 h-3 mr-1"></i> Verificado</span>`;
    } else if (tx.verification_status === 'SIMULATED') {
      statusBadge = `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"><i data-lucide="flask-conical" class="w-3 h-3 mr-1"></i> Simulado</span>`;
    } else if (tx.verification_status === 'UNCONFIRMED') {
      statusBadge = `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-500/10 text-slate-400 border border-slate-500/20"><i data-lucide="clock" class="w-3 h-3 mr-1"></i> Sin Confirmar</span>`;
    } else if (tx.verification_status === 'REJECTED') {
      statusBadge = `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-500/10 text-red-400 border border-red-500/20"><i data-lucide="x" class="w-3 h-3 mr-1"></i> Rechazado</span>`;
    } else if (tx.verification_status === 'DUPLICATE') {
      statusBadge = `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20"><i data-lucide="copy" class="w-3 h-3 mr-1"></i> Duplicado</span>`;
    }

    tr.innerHTML = `
      <td class="px-6 py-4 font-mono text-xs text-slate-400 whitespace-nowrap">${dateStr}</td>
      <td class="px-6 py-4">${bankBadge}</td>
      <td class="px-6 py-4 font-mono font-bold text-white">${tx.reference_number || 'N/A'}</td>
      <td class="px-6 py-4 font-bold text-slate-200">${formatCOP(tx.extracted_amount)}</td>
      <td class="px-6 py-4">${statusBadge}</td>
      <td class="px-6 py-4 text-right">
        <button onclick="openDetailModal('${tx.id}', '${tx.image_sha256}', '${tx.failure_reason || ''}')" class="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition">
          Forense
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  lucide.createIcons();
}

// Table Filters & Search
function setFilter(status) {
  currentFilter = status;
  ['ALL', 'VERIFIED', 'SIMULATED', 'REJECTED'].forEach(s => {
    const btn = document.getElementById(`filter-${s}`);
    if (!btn) return;
    if (s === status) {
      btn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500 text-slate-950 transition";
    } else {
      btn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-400 hover:text-white transition";
    }
  });
  filterTransactions();
}

function filterTransactions() {
  const query = document.getElementById('table-search').value.toLowerCase().trim();
  const filtered = allTransactions.filter(tx => {
    // Status Filter
    if (currentFilter !== 'ALL' && tx.verification_status !== currentFilter) {
      return false;
    }
    // Search Query
    if (query) {
      const matchRef = (tx.reference_number || '').toLowerCase().includes(query);
      const matchBank = (tx.bank_platform || '').toLowerCase().includes(query);
      const matchId = (tx.id || '').toLowerCase().includes(query);
      return matchRef || matchBank || matchId;
    }
    return true;
  });
  renderTransactions(filtered);
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
  setVerifyMode('simulate');
  lucide.createIcons();
});
