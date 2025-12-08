const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  // ============== Applications ==============

  // Fetch all applications
  getApplications: async () => {
    const response = await fetch(`${API_BASE_URL}/applications`);
    if (!response.ok) throw new Error('Failed to fetch applications');
    return response.json();
  },

  // Get single application with all related data
  getApplication: async (id) => {
    const response = await fetch(`${API_BASE_URL}/applications/${id}`);
    if (!response.ok) throw new Error('Failed to fetch application');
    return response.json();
  },

  // Create new application
  createApplication: async (data) => {
    const response = await fetch(`${API_BASE_URL}/applications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create application');
    return response.json();
  },

  // Update application
  updateApplication: async (id, data) => {
    const response = await fetch(`${API_BASE_URL}/applications/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update application');
    return response.json();
  },

  // Delete application
  deleteApplication: async (id) => {
    const response = await fetch(`${API_BASE_URL}/applications/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete application');
  },

  // ============== Job Details ==============

  // Create job details
  createJobDetails: async (applicationId, data) => {
    const response = await fetch(`${API_BASE_URL}/applications/${applicationId}/job-details`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create job details');
    return response.json();
  },

  // Update job details
  updateJobDetails: async (applicationId, data) => {
    const response = await fetch(`${API_BASE_URL}/applications/${applicationId}/job-details`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update job details');
    return response.json();
  },

  // ============== Notes ==============

  // Get all notes for an application
  getNotes: async (applicationId) => {
    const response = await fetch(`${API_BASE_URL}/applications/${applicationId}/notes`);
    if (!response.ok) throw new Error('Failed to fetch notes');
    return response.json();
  },

  // Create note
  createNote: async (applicationId, content) => {
    const response = await fetch(`${API_BASE_URL}/applications/${applicationId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) throw new Error('Failed to create note');
    return response.json();
  },

  // Update note
  updateNote: async (noteId, content) => {
    const response = await fetch(`${API_BASE_URL}/notes/${noteId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) throw new Error('Failed to update note');
    return response.json();
  },

  // Delete note
  deleteNote: async (noteId) => {
    const response = await fetch(`${API_BASE_URL}/notes/${noteId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete note');
  },

  // ============== Deadlines ==============

  // Get all deadlines for an application
  getDeadlines: async (applicationId) => {
    const response = await fetch(`${API_BASE_URL}/applications/${applicationId}/deadlines`);
    if (!response.ok) throw new Error('Failed to fetch deadlines');
    return response.json();
  },

  // Create deadline
  createDeadline: async (applicationId, data) => {
    const response = await fetch(`${API_BASE_URL}/applications/${applicationId}/deadlines`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create deadline');
    return response.json();
  },

  // Update deadline
  updateDeadline: async (deadlineId, data) => {
    const response = await fetch(`${API_BASE_URL}/deadlines/${deadlineId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update deadline');
    return response.json();
  },

  // Delete deadline
  deleteDeadline: async (deadlineId) => {
    const response = await fetch(`${API_BASE_URL}/deadlines/${deadlineId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete deadline');
  },

  // ============== Activities ==============

  // Get activity log for an application
  getActivities: async (applicationId) => {
    const response = await fetch(`${API_BASE_URL}/applications/${applicationId}/activities`);
    if (!response.ok) throw new Error('Failed to fetch activities');
    return response.json();
  },

  // ============== Scraping ==============

  // Scrape job URL
  scrapeUrl: async (url) => {
    const response = await fetch(`${API_BASE_URL}/scrape`, {
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

  // Export to Excel
  exportToExcel: async () => {
    const response = await fetch(`${API_BASE_URL}/export/excel`);
    if (!response.ok) throw new Error('Failed to export to Excel');
    return response.blob();
  },
};
