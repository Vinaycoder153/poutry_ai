const getBaseUrl = () => {
  // If VITE_API_URL is explicitly set at build time, use it
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL.replace(/\/$/, '');
  }
  
  // If running in browser, determine dynamically
  if (typeof window !== 'undefined') {
    const host = window.location.host;
    // If we're on localhost or Hugging Face directly, use relative paths
    if (host.includes('localhost') || host.includes('127.0.0.1') || host.includes('hf.space')) {
      return '';
    }
    // Otherwise, default to the production Hugging Face Spaces backend subdomain
    return 'https://vvvinay5630-poutry-ai.hf.space';
  }
  
  return '';
};

const API_URL = getBaseUrl();

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_URL}${endpoint}`;
    const response = await fetch(url, options);
    if (!response.ok) {
      const errorText = await response.text();
      let errorDetail = '';
      try {
        const errorJson = JSON.parse(errorText);
        errorDetail = errorJson.detail || errorJson.message || errorText;
      } catch (e) {
        errorDetail = errorText;
      }
      throw new Error(errorDetail || `HTTP Error ${response.status}`);
    }
    const data = await response.json();
    return this.sanitizeResponse(data);
  }

  sanitizeImageUrl(url) {
    if (!url) return url;
    // If it's a relative path, prefix it with API_URL or window location origin
    if (url.startsWith('/')) {
      return `${API_URL || window.location.origin}${url}`;
    }
    // If it's an absolute URL, check if it contains /uploads/
    if (url.includes('/uploads/')) {
      const parts = url.split('/uploads/');
      const filename = parts[parts.length - 1];
      return `${API_URL || window.location.origin}/uploads/${filename}`;
    }
    return url;
  }

  sanitizePrediction(pred) {
    if (!pred || typeof pred !== 'object') return pred;
    if (pred.image) {
      pred.image = this.sanitizeImageUrl(pred.image);
    }
    if (pred.originalImage) {
      pred.originalImage = this.sanitizeImageUrl(pred.originalImage);
    }
    return pred;
  }

  sanitizeResponse(data) {
    if (!data) return data;
    if (Array.isArray(data)) {
      return data.map(item => this.sanitizePrediction(item));
    }
    return this.sanitizePrediction(data);
  }

  getHealth() {
    return this.request('/api/health');
  }

  getHistory() {
    return this.request('/api/history');
  }

  deleteHistory(id) {
    return this.request(`/api/history/${id}`, { method: 'DELETE' });
  }

  toggleReviewed(id, reviewed) {
    return this.request(`/api/history/${id}/reviewed`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewed })
    });
  }

  toggleFlagged(id, flagged) {
    return this.request(`/api/history/${id}/flagged`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ flagged })
    });
  }

  submitCorrection(id, status) {
    return this.request(`/api/history/${id}/correct`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ correctedStatus: status })
    });
  }

  getNotifications() {
    return this.request('/api/notifications');
  }

  markNotificationRead(id, read) {
    return this.request(`/api/notifications/${id}/read`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ read })
    });
  }

  clearNotifications() {
    return this.request('/api/notifications/clear', { method: 'DELETE' });
  }

  getModelStatus() {
    return this.request('/api/model/status');
  }

  getModelLogs() {
    return this.request('/api/model/retrain/logs');
  }

  triggerRetrain() {
    return this.request('/api/model/retrain', { method: 'POST' });
  }

  async predictImage(file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request('/api/predict', {
      method: 'POST',
      body: formData
    });
  }
}

export const api = new ApiService();

