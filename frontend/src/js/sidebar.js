import { Auth, authApi } from './api.js';
import { initials } from './utils.js';

const NAV_ITEMS = [
  { href: 'dashboard.html', icon: gridIcon(),  label: 'Dashboard' },
  { href: 'calendar.html',  icon: calIcon(),   label: 'Kalendarz' },
  { href: 'budget.html',    icon: chartIcon(), label: 'Planer budżetu' },
  { href: 'groups.html',    icon: usersIcon(), label: 'Grupy' },
  { href: 'invoices.html',  icon: docIcon(),   label: 'Faktury' },
];

export function initDarkMode() {
  const t = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', t);
}

function toggleTheme() {
  const cur  = document.documentElement.getAttribute('data-theme') || 'light';
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  const btn = document.getElementById('themeToggleBtn');
  if (btn) btn.textContent = next === 'dark' ? '☀️ Jasny motyw' : '🌙 Ciemny motyw';
}

export function renderSidebar(activePage) {
  const user      = Auth.getUser();
  const sidebarEl = document.getElementById('sidebar');
  if (!sidebarEl) return;

  initDarkMode();
  const theme   = localStorage.getItem('theme') || 'light';
  const userName = user
    ? (user.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user.email)
    : '';

  const navHtml = NAV_ITEMS.map(item => `
    <a class="nav-item${activePage === item.href ? ' active' : ''}" href="${item.href}">
      ${item.icon}<span>${item.label}</span>
    </a>`).join('');

  const adminHtml = Auth.isAdmin() ? `
    <div class="sidebar-section-label">Admin</div>
    <a class="nav-item${activePage === 'admin.html' ? ' active' : ''}" href="admin.html">
      ${shieldIcon()}<span>Panel admina</span></a>` : '';

  sidebarEl.innerHTML = `
    <div class="sidebar-logo">
      <div class="sidebar-logo-mark">
        <div class="sidebar-logo-icon" style="border-radius:6px;overflow:hidden;background:#10b981;display:flex;align-items:center;justify-content:center">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="18" height="18">
            <rect width="32" height="32" rx="4" fill="#10b981"/>
            <text x="16" y="22" text-anchor="middle" font-family="Arial" font-weight="bold" font-size="18" fill="white">B</text>
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
      <a class="nav-item${activePage === 'profile.html' ? ' active' : ''}" href="profile.html">
        ${personIcon()}<span>Profil</span></a>
      ${adminHtml}
    </nav>

    <div class="sidebar-footer">
      <div id="sidebarUserCard" style="display:flex;align-items:center;gap:10px;padding:10px;border-radius:8px;cursor:pointer;transition:background 0.15s" onmouseenter="this.style.background='rgba(255,255,255,0.07)'" onmouseleave="this.style.background=''">
        <div class="avatar">${user ? initials(user.first_name, user.last_name, user.email) : '??'}</div>
        <div class="sidebar-user-info" style="flex:1;min-width:0">
          <div class="sidebar-user-name">${userName}</div>
          <div class="sidebar-user-role">${user?.role === 'admin' ? 'Administrator' : 'Użytkownik'}</div>
        </div>
        <svg width="12" height="12" viewBox="0 0 20 20" fill="rgba(255,255,255,0.3)">
          <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd"/>
        </svg>
      </div>

      <div id="sidebarPopup" style="display:none;background:rgba(255,255,255,0.06);border-radius:8px;margin-top:4px;overflow:hidden;border:1px solid rgba(255,255,255,0.1)">
        <a href="profile.html" style="display:flex;align-items:center;gap:8px;padding:10px 12px;color:var(--sidebar-text);text-decoration:none;font-size:13px" onmouseenter="this.style.background='rgba(255,255,255,0.08)'" onmouseleave="this.style.background=''">
          ${personIcon()} Ustawienia konta
        </a>
        <button id="themeToggleBtn" style="width:100%;display:flex;align-items:center;gap:8px;padding:10px 12px;color:var(--sidebar-text);background:transparent;border:none;font-size:13px;cursor:pointer;font-family:inherit;text-align:left" onmouseenter="this.style.background='rgba(255,255,255,0.08)'" onmouseleave="this.style.background=''">
          ${theme === 'dark' ? '☀️ Jasny motyw' : '🌙 Ciemny motyw'}
        </button>
        <div style="height:1px;background:rgba(255,255,255,0.07)"></div>
        <button id="sidebarLogoutBtn" style="width:100%;display:flex;align-items:center;gap:8px;padding:10px 12px;color:#f87171;background:transparent;border:none;font-size:13px;cursor:pointer;font-family:inherit;text-align:left" onmouseenter="this.style.background='rgba(248,113,113,0.08)'" onmouseleave="this.style.background=''">
          <svg width="13" height="13" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 4.25A2.25 2.25 0 015.25 2h5.5A2.25 2.25 0 0113 4.25v2a.75.75 0 01-1.5 0v-2a.75.75 0 00-.75-.75h-5.5a.75.75 0 00-.75.75v11.5c0 .414.336.75.75.75h5.5a.75.75 0 00.75-.75v-2a.75.75 0 011.5 0v2A2.25 2.25 0 0110.75 18h-5.5A2.25 2.25 0 013 15.75V4.25z" clip-rule="evenodd"/><path fill-rule="evenodd" d="M6 10a.75.75 0 01.75-.75h9.546l-1.048-.943a.75.75 0 111.004-1.114l2.5 2.25a.75.75 0 010 1.114l-2.5 2.25a.75.75 0 11-1.004-1.114l1.048-.943H6.75A.75.75 0 016 10z" clip-rule="evenodd"/></svg>
          Wyloguj się
        </button>
      </div>

      <div style="padding:8px 10px;font-size:10.5px;color:rgba(255,255,255,0.2);line-height:1.5;text-align:center;margin-top:4px">
        Projekt edukacyjny.<br>Twórcy nie ponoszą odpowiedzialności<br>za szkody wynikłe z użytkowania.
      </div>
    </div>
  `;

  // Popup — proste toggle bez event bubbling problemów
  const card  = document.getElementById('sidebarUserCard');
  const popup = document.getElementById('sidebarPopup');

  card.onclick = function() {
    popup.style.display = popup.style.display === 'block' ? 'none' : 'block';
  };

  document.getElementById('themeToggleBtn').onclick = function() {
    toggleTheme();
    popup.style.display = 'none';
  };

  document.getElementById('sidebarLogoutBtn').onclick = function() {
    popup.style.display = 'none';
    if (confirm('Czy na pewno chcesz się wylogować?')) authApi.logout();
  };

  // Zamknij popup przy kliknięciu poza sidebar
  document.addEventListener('click', function handler(e) {
    if (!sidebarEl.contains(e.target)) {
      popup.style.display = 'none';
    }
  });

  document.getElementById('menuBtn')?.addEventListener('click', () => sidebarEl.classList.toggle('open'));
}

function gridIcon()   { return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.25 2A2.25 2.25 0 002 4.25v2.5A2.25 2.25 0 004.25 9h2.5A2.25 2.25 0 009 6.75v-2.5A2.25 2.25 0 006.75 2h-2.5zm0 9A2.25 2.25 0 002 13.25v2.5A2.25 2.25 0 004.25 18h2.5A2.25 2.25 0 009 15.75v-2.5A2.25 2.25 0 006.75 11h-2.5zm6.5-9A2.25 2.25 0 0011 4.25v2.5A2.25 2.25 0 0013.25 9h2.5A2.25 2.25 0 0018 6.75v-2.5A2.25 2.25 0 0015.75 2h-2.5zm0 9A2.25 2.25 0 0011 13.25v2.5A2.25 2.25 0 0013.25 18h2.5A2.25 2.25 0 0018 15.75v-2.5A2.25 2.25 0 0015.75 11h-2.5z" clip-rule="evenodd"/></svg>`; }
function calIcon()    { return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5.75 2a.75.75 0 01.75.75V4h7V2.75a.75.75 0 011.5 0V4h.25A2.75 2.75 0 0118 6.75v8.5A2.75 2.75 0 0115.25 18H4.75A2.75 2.75 0 012 15.25v-8.5A2.75 2.75 0 014.75 4H5V2.75A.75.75 0 015.75 2zm-1 5.5c-.69 0-1.25.56-1.25 1.25v6.5c0 .69.56 1.25 1.25 1.25h10.5c.69 0 1.25-.56 1.25-1.25v-6.5c0-.69-.56-1.25-1.25-1.25H4.75z" clip-rule="evenodd"/></svg>`; }
function chartIcon()  { return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path d="M15.5 2A1.5 1.5 0 0014 3.5v13a1.5 1.5 0 003 0v-13A1.5 1.5 0 0015.5 2zM9.5 6A1.5 1.5 0 008 7.5v9a1.5 1.5 0 003 0v-9A1.5 1.5 0 009.5 6zM3.5 10A1.5 1.5 0 002 11.5v5a1.5 1.5 0 003 0v-5A1.5 1.5 0 003.5 10z"/></svg>`; }
function usersIcon()  { return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path d="M7 8a3 3 0 100-6 3 3 0 000 6zM14.5 9a2.5 2.5 0 100-5 2.5 2.5 0 000 5zM1.615 16.428a1.224 1.224 0 01-.569-1.175 6.002 6.002 0 0111.908 0c.058.467-.172.92-.57 1.174A9.953 9.953 0 017 18a9.953 9.953 0 01-5.385-1.572zM14.5 16h-.106c.07-.297.088-.611.048-.933a7.47 7.47 0 00-1.588-3.755 4.502 4.502 0 015.874 2.636.818.818 0 01-.36.98A7.465 7.465 0 0114.5 16z"/></svg>`; }
function docIcon()    { return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.5 2A1.5 1.5 0 003 3.5v13A1.5 1.5 0 004.5 18h11a1.5 1.5 0 001.5-1.5V7.621a1.5 1.5 0 00-.44-1.06l-4.12-4.122A1.5 1.5 0 0011.378 2H4.5zm2.25 8.5a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5zm0 3a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5zm0-6a.75.75 0 000 1.5h3a.75.75 0 000-1.5h-3z" clip-rule="evenodd"/></svg>`; }
function personIcon() { return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path d="M10 8a3 3 0 100-6 3 3 0 000 6zM3.465 14.493a1.23 1.23 0 00.41 1.412A9.957 9.957 0 0010 18c2.31 0 4.438-.784 6.131-2.1.43-.333.604-.903.408-1.41a7.002 7.002 0 00-13.074.003z"/></svg>`; }
function shieldIcon() { return `<svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9.661 2.237a.531.531 0 01.678 0 11.947 11.947 0 007.078 2.749.5.5 0 01.479.425c.069.52.104 1.05.104 1.589 0 5.162-3.26 9.563-7.834 11.256a.48.48 0 01-.332 0C5.26 16.563 2 12.162 2 7c0-.538.035-1.069.104-1.589a.5.5 0 01.48-.425 11.947 11.947 0 007.077-2.75z" clip-rule="evenodd"/></svg>`; }
