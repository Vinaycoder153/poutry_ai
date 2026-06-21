const API_URL = import.meta.env.VITE_API_URL || '';

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
    return response.json();
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
