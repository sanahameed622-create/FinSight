/**
 * FinSight API Client & Utility Functions
 */

const API_BASE = '/api';

const Api = {
  getToken() {
    return localStorage.getItem('finsight_token');
  },

  setToken(token) {
    localStorage.setItem('finsight_token', token);
  },

  getUser() {
    const userStr = localStorage.getItem('finsight_user');
    return userStr ? JSON.parse(userStr) : null;
  },

  setUser(user, businessName) {
    localStorage.setItem('finsight_user', JSON.stringify(user));
    if (businessName) {
      localStorage.setItem('finsight_business', businessName);
    }
  },

  getBusinessName() {
    return localStorage.getItem('finsight_business') || 'FinSight Workspace';
  },

  clearSession() {
    localStorage.removeItem('finsight_token');
    localStorage.removeItem('finsight_user');
    localStorage.removeItem('finsight_business');
  },

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, { ...options, headers });

      if (response.status === 401) {
        // Unauthorized - session expired
        this.clearSession();
        if (!window.location.pathname.endsWith('login.html') && !window.location.pathname.endsWith('register.html') && window.location.pathname !== '/') {
          window.location.href = 'login.html';
        }
        throw new Error('Session expired. Please log in again.');
      }

      // Check if download / blob
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('text/csv')) {
        return await response.blob();
      }

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'An error occurred while processing your request.');
      }

      return data;
    } catch (err) {
      console.error('API Error:', err);
      throw err;
    }
  },

  get(endpoint, params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `${endpoint}?${query}` : endpoint;
    return this.request(url, { method: 'GET' });
  },

  post(endpoint, body) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },

  put(endpoint, body) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body)
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
};

// PKR Currency Formatter
function formatPKR(val) {
  if (val === null || val === undefined || isNaN(val)) return 'Rs. 0';
  return 'Rs. ' + Number(val).toLocaleString('en-PK', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  });
}

function formatDate(isoStr) {
  if (!isoStr) return '-';
  const d = new Date(isoStr);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}
