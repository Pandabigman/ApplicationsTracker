const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Returns the URL only if it uses http or https, otherwise null.
 * Prevents javascript: and other dangerous protocol XSS via href attributes.
 */
export function safeHref(url) {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return null;
    return url;
  } catch {
    return null;
  }
}

// Auth token getter - set by useAuthSetup() in React
let _getToken = null;

export const setAuthTokenGetter = (getter) => {
  _getToken = getter;
};

async function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (_getToken) {
    const token = await _getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return headers;
}

async function authFetch(url, options = {}) {
  const headers = await authHeaders(options.headers || {});
  const response = await fetch(url, { ...options, headers });
  return response;
}

export const api = {
  // ============== Applications ==============

  getApplications: async () => {
    const response = await authFetch(`${API_BASE_URL}/applications`);
    if (!response.ok) throw new Error('Failed to fetch applications');
    return response.json();
  },

  getApplication: async (id) => {
    const response = await authFetch(`${API_BASE_URL}/applications/${id}`);
    if (!response.ok) throw new Error('Failed to fetch application');
    return response.json();
  },

  createApplication: async (data) => {
    const response = await authFetch(`${API_BASE_URL}/applications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create application');
    return response.json();
  },

  updateApplication: async (id, data) => {
    const response = await authFetch(`${API_BASE_URL}/applications/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update application');
    return response.json();
  },

  deleteApplication: async (id) => {
    const response = await authFetch(`${API_BASE_URL}/applications/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete application');
  },

  // ============== Job Details ==============

  createJobDetails: async (applicationId, data) => {
    const response = await authFetch(`${API_BASE_URL}/applications/${applicationId}/job-details`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create job details');
    return response.json();
  },

  updateJobDetails: async (applicationId, data) => {
    const response = await authFetch(`${API_BASE_URL}/applications/${applicationId}/job-details`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update job details');
    return response.json();
  },

  // ============== Notes ==============

  getNotes: async (applicationId) => {
    const response = await authFetch(`${API_BASE_URL}/applications/${applicationId}/notes`);
    if (!response.ok) throw new Error('Failed to fetch notes');
    return response.json();
  },

  createNote: async (applicationId, content) => {
    const response = await authFetch(`${API_BASE_URL}/applications/${applicationId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) throw new Error('Failed to create note');
    return response.json();
  },

  updateNote: async (noteId, content) => {
    const response = await authFetch(`${API_BASE_URL}/notes/${noteId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) throw new Error('Failed to update note');
    return response.json();
  },

  deleteNote: async (noteId) => {
    const response = await authFetch(`${API_BASE_URL}/notes/${noteId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete note');
  },

  // ============== Deadlines ==============

  getDeadlines: async (applicationId) => {
    const response = await authFetch(`${API_BASE_URL}/applications/${applicationId}/deadlines`);
    if (!response.ok) throw new Error('Failed to fetch deadlines');
    return response.json();
  },

  createDeadline: async (applicationId, data) => {
    const response = await authFetch(`${API_BASE_URL}/applications/${applicationId}/deadlines`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create deadline');
    return response.json();
  },

  updateDeadline: async (deadlineId, data) => {
    const response = await authFetch(`${API_BASE_URL}/deadlines/${deadlineId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update deadline');
    return response.json();
  },

  deleteDeadline: async (deadlineId) => {
    const response = await authFetch(`${API_BASE_URL}/deadlines/${deadlineId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete deadline');
  },

  // ============== Activities ==============

  getActivities: async (applicationId) => {
    const response = await authFetch(`${API_BASE_URL}/applications/${applicationId}/activities`);
    if (!response.ok) throw new Error('Failed to fetch activities');
    return response.json();
  },

  // ============== Scraping ==============

  scrapeUrl: async (url) => {
    const response = await authFetch(`${API_BASE_URL}/scrape`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to scrape URL');
    }
    return response.json();
  },

  // ============== Export ==============

  exportToExcel: async () => {
    const response = await authFetch(`${API_BASE_URL}/export/excel`);
    if (!response.ok) throw new Error('Failed to export to Excel');
    return response.blob();
  },
};
