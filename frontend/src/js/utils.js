/**
 * utils.js — formaty, toasty, helpery UI
 */

// ── Formatters ──────────────────────────────────────────────────
export function formatCurrency(amount, currency = 'PLN') {
  return new Intl.NumberFormat('pl-PL', {
    style: 'currency', currency, minimumFractionDigits: 2,
  }).format(Number(amount) || 0);
}

export function formatDate(dateStr, opts = {}) {
  if (!dateStr) return '—';
  return new Intl.DateTimeFormat('pl-PL', {
    day: '2-digit', month: 'short', year: 'numeric', ...opts,
  }).format(new Date(dateStr));
}

export function formatDateShort(dateStr) {
  if (!dateStr) return '—';
  return new Intl.DateTimeFormat('pl-PL', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  }).format(new Date(dateStr));
}

export function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  return new Intl.DateTimeFormat('pl-PL', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  }).format(new Date(dateStr));
}

export function formatMonthYear(dateStr) {
  const d = dateStr ? new Date(dateStr) : new Date();
  return new Intl.DateTimeFormat('pl-PL', { month: 'long', year: 'numeric' }).format(d);
}

export function initials(firstName, lastName, email) {
  if (firstName && lastName) return `${firstName[0]}${lastName[0]}`.toUpperCase();
  if (firstName)             return firstName.slice(0, 2).toUpperCase();
  if (email)                 return email.slice(0, 2).toUpperCase();
  return '??';
}

export function relativeTime(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1)   return 'przed chwilą';
  if (m < 60)  return `${m} min temu`;
  const h = Math.floor(m / 60);
  if (h < 24)  return `${h} godz. temu`;
  const d = Math.floor(h / 24);
  return `${d} dni temu`;
}

// ── Toast ────────────────────────────────────────────────────────
let _toastContainer = null;

function getToastContainer() {
  if (!_toastContainer) {
    _toastContainer = document.createElement('div');
    _toastContainer.className = 'toast-container';
    document.body.appendChild(_toastContainer);
  }
  return _toastContainer;
}

const ICONS = {
  success: `<svg viewBox="0 0 20 20" fill="currentColor" class="toast-icon" style="color:#10b981"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/></svg>`,
  error:   `<svg viewBox="0 0 20 20" fill="currentColor" class="toast-icon" style="color:#ef4444"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/></svg>`,
  warning: `<svg viewBox="0 0 20 20" fill="currentColor" class="toast-icon" style="color:#f59e0b"><path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/></svg>`,
  info:    `<svg viewBox="0 0 20 20" fill="currentColor" class="toast-icon" style="color:#3b82f6"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clip-rule="evenodd"/></svg>`,
};

export function toast(message, type = 'info', duration = 3500) {
  const container = getToastContainer();
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `${ICONS[type] || ''}<span>${message}</span>`;
  container.appendChild(el);
  setTimeout(() => {
    el.style.animation = 'toastOut 0.25s ease forwards';
    setTimeout(() => el.remove(), 250);
  }, duration);
}

export const showSuccess = (msg) => toast(msg, 'success');
export const showError   = (msg) => toast(msg, 'error');
export const showWarning = (msg) => toast(msg, 'warning');
export const showInfo    = (msg) => toast(msg, 'info');

// ── Modal helpers ────────────────────────────────────────────────
export function openModal(overlay) {
  overlay.classList.remove('hidden');
  requestAnimationFrame(() => overlay.classList.add('open'));
  document.body.style.overflow = 'hidden';
}

export function closeModal(overlay) {
  overlay.classList.remove('open');
  document.body.style.overflow = '';
  setTimeout(() => overlay.classList.add('hidden'), 200);
}

export function confirmDialog(message, title = 'Potwierdź') {
  return new Promise(resolve => {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay hidden';
    overlay.innerHTML = `
      <div class="modal" style="max-width:380px">
        <div class="modal-header">
          <span class="modal-title">${title}</span>
        </div>
        <p style="font-size:14px;color:var(--text-secondary);line-height:1.6">${message}</p>
        <div class="modal-footer">
          <button class="btn btn-secondary btn-sm" id="_cancel">Anuluj</button>
          <button class="btn btn-danger btn-sm" id="_confirm">Usuń</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    openModal(overlay);
    overlay.querySelector('#_cancel').onclick  = () => { closeModal(overlay); setTimeout(() => overlay.remove(), 250); resolve(false); };
    overlay.querySelector('#_confirm').onclick = () => { closeModal(overlay); setTimeout(() => overlay.remove(), 250); resolve(true); };
  });
}

// ── Form helpers ─────────────────────────────────────────────────
export function getFormData(form) {
  const data = {};
  new FormData(form).forEach((v, k) => { data[k] = v; });
  return data;
}

export function setLoading(btn, loading, text = btn.textContent) {
  if (loading) {
    btn._orig = btn.innerHTML;
    btn.innerHTML = `<span class="spinner" style="width:14px;height:14px;border-width:1.5px"></span>`;
    btn.disabled = true;
  } else {
    btn.innerHTML = btn._orig || text;
    btn.disabled = false;
  }
}

// ── Auth guard ──────────────────────────────────────────────────
export function requireAuth() {
  const { Auth } = window._api || {};
  const token = localStorage.getItem('access_token');
  if (!token) {
    window.location.href = '/pages/login.html';
    return false;
  }
  return true;
}

export function requireAdmin() {
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  if (!user || user.role !== 'admin') {
    window.location.href = '/pages/dashboard.html';
    return false;
  }
  return true;
}

// ── Sidebar active state ─────────────────────────────────────────
export function setActiveNav(href) {
  document.querySelectorAll('.nav-item[data-href]').forEach(item => {
    item.classList.toggle('active', item.dataset.href === href);
  });
}

// ── Current period ──────────────────────────────────────────────
export function currentPeriod() {
  const now = new Date();
  return { year: now.getFullYear(), month: now.getMonth() + 1 };
}

// ── Color for category icon ─────────────────────────────────────
export const CATEGORY_COLORS = [
  '#10b981','#3b82f6','#f59e0b','#ef4444',
  '#8b5cf6','#ec4899','#14b8a6','#f97316',
  '#6366f1','#84cc16',
];

export function categoryBg(color) {
  return color ? `${color}20` : '#f3f4f6';
}
