/**
 * sidebar.js — renderuje sidebar i obsługuje nawigację
 */

import { Auth, authApi } from './api.js';
import { initials } from './utils.js';

const NAV_ITEMS = [
  { href: 'dashboard.html', icon: gridIcon(),    label: 'Dashboard' },
  { href: 'calendar.html',  icon: calIcon(),     label: 'Kalendarz' },
  { href: 'budget.html',    icon: chartIcon(),   label: 'Planer budżetu' },
  { href: 'groups.html',    icon: usersIcon(),   label: 'Grupy' },
  { href: 'invoices.html',  icon: docIcon(),     label: 'Faktury' },
];

const ACCOUNT_ITEMS = [
  { href: 'profile.html', icon: personIcon(), label: 'Profil' },
];

export function renderSidebar(activePage) {
  const user = Auth.getUser();
  const sidebarEl = document.getElementById('sidebar');
  if (!sidebarEl) return;

  const navHtml = NAV_ITEMS.map(item => `
    <a class="nav-item${activePage === item.href ? ' active' : ''}" 
       data-href="${item.href}" href="${item.href}">
      ${item.icon}
      <span>${item.label}</span>
    </a>
  `).join('');

  const accountHtml = ACCOUNT_ITEMS.map(item => `
    <a class="nav-item${activePage === item.href ? ' active' : ''}"
       data-href="${item.href}" href="${item.href}">
      ${item.icon}
      <span>${item.label}</span>
    </a>
  `).join('');

  const adminHtml = Auth.isAdmin() ? `
    <div class="sidebar-section-label">Admin</div>
    <a class="nav-item${activePage === 'admin.html' ? ' active' : ''}"
       data-href="admin.html" href="admin.html">
      ${shieldIcon()}
      <span>Panel admina</span>
    </a>
  ` : '';

  sidebarEl.innerHTML = `
    <div class="sidebar-logo">
      <div class="sidebar-logo-mark">
        <div class="sidebar-logo-icon">
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.75 10.818v2.614A3.13 3.13 0 0011.888 13c.482-.315.612-.648.612-.875 0-.227-.13-.56-.612-.875a3.13 3.13 0 00-1.138-.432zM8.33 8.62c.053.055.115.11.184.164.208.16.46.284.736.363V6.603a2.45 2.45 0 00-.35.13c-.14.065-.27.143-.386.233-.377.292-.514.627-.514.909 0 .184.058.39.33.585z"/>
            <path fill-rule="evenodd" d="M9.99 1.012C5.042 1.012 1 5.058 1 10c0 4.946 4.042 8.988 8.99 8.988C14.952 18.988 19 14.946 19 10c0-4.942-4.048-8.988-9.01-8.988zM10 5.5a.75.75 0 01.75.75v.807a4.62 4.62 0 011.743.733 3.257 3.257 0 011.007 1.29.75.75 0 01-1.39.567 1.757 1.757 0 00-.537-.698 3.12 3.12 0 00-.823-.407v2.3l.427.109c.31.079.633.181.93.352.298.172.578.417.79.748.214.334.353.74.353 1.249 0 .562-.181 1.077-.508 1.508-.316.42-.761.733-1.282.938a4.63 4.63 0 01-.71.189V14.5a.75.75 0 01-1.5 0v-.806a4.944 4.944 0 01-1.793-.762 3.515 3.515 0 01-1.143-1.422.75.75 0 011.393-.553c.14.356.367.638.648.84.297.214.665.364 1.095.454V9.937l-.308-.079a5.284 5.284 0 01-.994-.371 3.173 3.173 0 01-.84-.65C7.293 8.478 7 7.97 7 7.25c0-.546.178-1.04.488-1.455.306-.41.734-.718 1.228-.918A4.64 4.64 0 0110 4.75V5.5z" clip-rule="evenodd"/>
          </svg>
        </div>
        <div>
          <div class="sidebar-logo-text">BudzetApp</div>
          <div class="sidebar-logo-sub">Zarządzaj finansami</div>
        </div>
      </div>
    </div>

    <nav class="sidebar-nav">
      ${navHtml}
      <div class="sidebar-section-label">Konto</div>
      ${accountHtml}
      ${adminHtml}
    </nav>

    <div class="sidebar-footer">
      <div class="sidebar-user" id="sidebarLogout" title="Wyloguj się">
        <div class="avatar" id="sidebarAvatar">${user ? initials(user.first_name, user.last_name, user.email) : '??'}</div>
        <div class="sidebar-user-info">
          <div class="sidebar-user-name" id="sidebarUserName">
            ${user ? (user.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user.email) : ''}
          </div>
          <div class="sidebar-user-role">${user?.role === 'admin' ? 'Administrator' : 'Użytkownik'}</div>
        </div>
        <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" style="color:rgba(255,255,255,0.3);flex-shrink:0">
          <path d="M15.75 9H5.25M10.5 3.75L5.25 9l5.25 5.25" stroke-linecap="round" stroke-linejoin="round" transform="rotate(180 10 10)"/>
        </svg>
      </div>
    </div>
  `;

  // Logout handler
  document.getElementById('sidebarLogout')?.addEventListener('click', () => {
    if (confirm('Czy na pewno chcesz się wylogować?')) {
      authApi.logout();
    }
  });

  // Mobile burger
  document.getElementById('menuBtn')?.addEventListener('click', () => {
    sidebarEl.classList.toggle('open');
  });
}

// ── Icons (inline SVG) ───────────────────────────────────────────
function gridIcon() {
  return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.25 2A2.25 2.25 0 002 4.25v2.5A2.25 2.25 0 004.25 9h2.5A2.25 2.25 0 009 6.75v-2.5A2.25 2.25 0 006.75 2h-2.5zm0 9A2.25 2.25 0 002 13.25v2.5A2.25 2.25 0 004.25 18h2.5A2.25 2.25 0 009 15.75v-2.5A2.25 2.25 0 006.75 11h-2.5zm6.5-9A2.25 2.25 0 0011 4.25v2.5A2.25 2.25 0 0013.25 9h2.5A2.25 2.25 0 0018 6.75v-2.5A2.25 2.25 0 0015.75 2h-2.5zm0 9A2.25 2.25 0 0011 13.25v2.5A2.25 2.25 0 0013.25 18h2.5A2.25 2.25 0 0018 15.75v-2.5A2.25 2.25 0 0015.75 11h-2.5z" clip-rule="evenodd"/></svg>`;
}
function calIcon() {
  return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5.75 2a.75.75 0 01.75.75V4h7V2.75a.75.75 0 011.5 0V4h.25A2.75 2.75 0 0118 6.75v8.5A2.75 2.75 0 0115.25 18H4.75A2.75 2.75 0 012 15.25v-8.5A2.75 2.75 0 014.75 4H5V2.75A.75.75 0 015.75 2zm-1 5.5c-.69 0-1.25.56-1.25 1.25v6.5c0 .69.56 1.25 1.25 1.25h10.5c.69 0 1.25-.56 1.25-1.25v-6.5c0-.69-.56-1.25-1.25-1.25H4.75z" clip-rule="evenodd"/></svg>`;
}
function chartIcon() {
  return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path d="M15.5 2A1.5 1.5 0 0014 3.5v13a1.5 1.5 0 003 0v-13A1.5 1.5 0 0015.5 2zM9.5 6A1.5 1.5 0 008 7.5v9a1.5 1.5 0 003 0v-9A1.5 1.5 0 009.5 6zM3.5 10A1.5 1.5 0 002 11.5v5a1.5 1.5 0 003 0v-5A1.5 1.5 0 003.5 10z"/></svg>`;
}
function usersIcon() {
  return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path d="M7 8a3 3 0 100-6 3 3 0 000 6zM14.5 9a2.5 2.5 0 100-5 2.5 2.5 0 000 5zM1.615 16.428a1.224 1.224 0 01-.569-1.175 6.002 6.002 0 0111.908 0c.058.467-.172.92-.57 1.174A9.953 9.953 0 017 18a9.953 9.953 0 01-5.385-1.572zM14.5 16h-.106c.07-.297.088-.611.048-.933a7.47 7.47 0 00-1.588-3.755 4.502 4.502 0 015.874 2.636.818.818 0 01-.36.98A7.465 7.465 0 0114.5 16z"/></svg>`;
}
function docIcon() {
  return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.5 2A1.5 1.5 0 003 3.5v13A1.5 1.5 0 004.5 18h11a1.5 1.5 0 001.5-1.5V7.621a1.5 1.5 0 00-.44-1.06l-4.12-4.122A1.5 1.5 0 0011.378 2H4.5zm2.25 8.5a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5zm0 3a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5zm0-6a.75.75 0 000 1.5h3a.75.75 0 000-1.5h-3z" clip-rule="evenodd"/></svg>`;
}
function personIcon() {
  return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path d="M10 8a3 3 0 100-6 3 3 0 000 6zM3.465 14.493a1.23 1.23 0 00.41 1.412A9.957 9.957 0 0010 18c2.31 0 4.438-.784 6.131-2.1.43-.333.604-.903.408-1.41a7.002 7.002 0 00-13.074.003z"/></svg>`;
}
function shieldIcon() {
  return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9.661 2.237a.531.531 0 01.678 0 11.947 11.947 0 007.078 2.749.5.5 0 01.479.425c.069.52.104 1.05.104 1.589 0 5.162-3.26 9.563-7.834 11.256a.48.48 0 01-.332 0C5.26 16.563 2 12.162 2 7c0-.538.035-1.069.104-1.589a.5.5 0 01.48-.425 11.947 11.947 0 007.077-2.75z" clip-rule="evenodd"/></svg>`;
}
