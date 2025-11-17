const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  // Fetch all applications
  getApplications: async () => {
    const response = await fetch(`${API_BASE_URL}/applications`);
    if (!response.ok) throw new Error('Failed to fetch applications');
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

  // Export to Excel
  exportToExcel: async () => {
    const response = await fetch(`${API_BASE_URL}/export/excel`);
    if (!response.ok) throw new Error('Failed to export to Excel');
    return response.blob();
  },
};