/**
 * api.js — Fetch wrapper z automatycznym odświeżaniem tokenu JWT
 */

const API_BASE = '/api';

// ── Token management ────────────────────────────────────────────
export const Auth = {
  getAccessToken:  () => localStorage.getItem('access_token'),
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  setTokens(access, refresh) {
    localStorage.setItem('access_token', access);
    if (refresh) localStorage.setItem('refresh_token', refresh);
  },
  clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
  getUser()  { return JSON.parse(localStorage.getItem('user') || 'null'); },
  setUser(u) { localStorage.setItem('user', JSON.stringify(u)); },
  isLoggedIn() { return !!this.getAccessToken(); },
  isAdmin()    { return this.getUser()?.role === 'admin'; },
};

// ── Base fetch ──────────────────────────────────────────────────
let _refreshPromise = null;

async function _refreshToken() {
  if (_refreshPromise) return _refreshPromise;
  _refreshPromise = (async () => {
    const rt = Auth.getRefreshToken();
    if (!rt) throw new Error('No refresh token');
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${rt}`,
      },
    });
    if (!res.ok) throw new Error('Refresh failed');
    const { access_token } = await res.json();
    Auth.setTokens(access_token, null);
    return access_token;
  })();
  try {
    return await _refreshPromise;
  } finally {
    _refreshPromise = null;
  }
}

async function request(path, options = {}, retry = true) {
  const token = Auth.getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...(options.headers || {}),
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  // Auto-refresh on 401
  if (res.status === 401 && retry) {
    try {
      await _refreshToken();
      return request(path, options, false);
    } catch {
      Auth.clearTokens();
      window.location.href = '/pages/login.html';
      throw new Error('Session expired');
    }
  }

  // 204 No Content
  if (res.status === 204) return null;

  const data = await res.json();
  if (!res.ok) {
    const err = new Error(data.error || data.message || `HTTP ${res.status}`);
    err.status = res.status;
    err.data   = data;
    throw err;
  }
  return data;
}

// ── HTTP methods ────────────────────────────────────────────────
export const api = {
  get:    (path, params) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return request(path + qs);
  },
  post:   (path, body) => request(path, { method: 'POST',   body: JSON.stringify(body) }),
  put:    (path, body) => request(path, { method: 'PUT',    body: JSON.stringify(body) }),
  patch:  (path, body) => request(path, { method: 'PATCH',  body: JSON.stringify(body) }),
  delete: (path)       => request(path, { method: 'DELETE' }),
};

// ── Auth endpoints ──────────────────────────────────────────────
export const authApi = {
  async login(email, password) {
    const data = await api.post('/auth/login', { email, password });
    Auth.setTokens(data.access_token, data.refresh_token);
    Auth.setUser(data.user);
    return data;
  },
  async register(payload) {
    const data = await api.post('/auth/register', payload);
    Auth.setTokens(data.access_token, data.refresh_token);
    Auth.setUser(data.user);
    return data;
  },
  async logout() {
    try { await api.post('/auth/logout'); } catch {}
    Auth.clearTokens();
    window.location.href = '/pages/login.html';
  },
  me: () => api.get('/auth/me'),
};

// ── Budget endpoints ────────────────────────────────────────────
export const budgetApi = {
  summary:    (params) => api.get('/budget/summary',     params),
  chart:      (params) => api.get('/budget/chart',       params),
  byCategory: (params) => api.get('/budget/by-category', params),
  recurring:  ()       => api.get('/budget/recurring'),
  forecast:   (params) => api.get('/budget/forecast',    params),
};

// ── Transactions ────────────────────────────────────────────────
export const txApi = {
  list:   (params) => api.get('/transactions/', params),
  create: (body)   => api.post('/transactions/', body),
  update: (id, b)  => api.put(`/transactions/${id}`, b),
  delete: (id)     => api.delete(`/transactions/${id}`),
};

// ── Events ──────────────────────────────────────────────────────
export const eventsApi = {
  list:   (params) => api.get('/events/', params),
  create: (body)   => api.post('/events/', body),
  update: (id, b)  => api.put(`/events/${id}`, b),
  delete: (id)     => api.delete(`/events/${id}`),
};

// ── Groups ──────────────────────────────────────────────────────
export const groupsApi = {
  list:          ()       => api.get('/groups/'),
  create:        (b)      => api.post('/groups/', b),
  get:           (id)     => api.get(`/groups/${id}`),
  update:        (id, b)  => api.put(`/groups/${id}`, b),
  delete:        (id)     => api.delete(`/groups/${id}`),
  listMembers:   (id)     => api.get(`/groups/${id}/members`),
  invite:        (id, b)  => api.post(`/groups/${id}/members`, b),
  updateRole:    (gid, uid, b) => api.put(`/groups/${gid}/members/${uid}`, b),
  removeMember:  (gid, uid)   => api.delete(`/groups/${gid}/members/${uid}`),
  leave:         (id)     => api.post(`/groups/${id}/leave`),
  transactions:  (id, p)  => api.get(`/groups/${id}/transactions`, p),
  summary:       (id)     => api.get(`/groups/${id}/summary`),
};

// ── Invoices ────────────────────────────────────────────────────
export const invoicesApi = {
  list:        (params) => api.get('/invoices/', params),
  create:      (body)   => api.post('/invoices/', body),
  get:         (id)     => api.get(`/invoices/${id}`),
  update:      (id, b)  => api.put(`/invoices/${id}`, b),
  delete:      (id)     => api.delete(`/invoices/${id}`),
  setStatus:   (id, s)  => api.patch(`/invoices/${id}/status`, { status: s }),
  pdfUrl:      (id)     => `${API_BASE}/invoices/${id}/pdf`,
  send:        (id)     => api.post(`/invoices/${id}/send`),
};

// ── Categories ──────────────────────────────────────────────────
export const categoriesApi = {
  list:   (params) => api.get('/categories/', params),
  create: (body)   => api.post('/categories/', body),
  update: (id, b)  => api.put(`/categories/${id}`, b),
  delete: (id)     => api.delete(`/categories/${id}`),
};

// ── Admin ────────────────────────────────────────────────────────
export const adminApi = {
  stats:            ()        => api.get('/admin/stats'),
  users:            (params)  => api.get('/admin/users', params),
  updateUser:       (id, b)   => api.patch(`/admin/users/${id}`, b),
  deleteUser:       (id)      => api.delete(`/admin/users/${id}`),
  transactions:     (params)  => api.get('/admin/transactions', params),
  events:           (params)  => api.get('/admin/events', params),
  deleteEvent:      (id)      => api.delete(`/admin/events/${id}`),
};
