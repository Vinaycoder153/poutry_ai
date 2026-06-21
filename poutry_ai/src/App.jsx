import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Auth from './pages/Auth';
import Dashboard from './pages/Dashboard';
import ImageUpload from './pages/ImageUpload';
import AnalysisResults from './pages/AnalysisResults';
import History from './pages/History';
import Community from './pages/Community';
import Settings from './pages/Settings';
import ModelCenter from './pages/ModelCenter';
import { X, ShieldAlert, AlertTriangle } from 'lucide-react';

// Reusable SVG drawings for pre-seeded history items
const SVG_HEALTHY = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect width="400" height="300" fill="%23f3f4f6"/><ellipse cx="200" cy="150" rx="30" ry="25" fill="%23fda4af" fill-opacity="0.6" stroke="%23f43f5e"/><circle cx="200" cy="150" r="8" fill="%23e11d48"/><text x="200" y="270" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="14" fill="%234b5563">Preset: Normal healthy vent</text></svg>`;
const SVG_WARNING = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect width="400" height="300" fill="%23f3f4f6"/><path d="M160,110 C170,115 180,105 185,115" stroke="%23d97706" fill="none" stroke-width="6"/><ellipse cx="200" cy="150" rx="32" ry="26" fill="%23fecdd3" fill-opacity="0.8" stroke="%23e11d48"/><circle cx="200" cy="150" r="10" fill="%23be123c"/><text x="200" y="270" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="14" fill="%234b5563">Preset: Mild Pasting &amp; Redness</text></svg>`;
const SVG_DANGER = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect width="400" height="300" fill="%23f3f4f6"/><path d="M170,170 C165,200 175,220 170,230" stroke="%23ca8a04" fill="none" stroke-width="8"/><ellipse cx="200" cy="150" rx="35" ry="28" fill="%23fda4af" fill-opacity="0.9" stroke="%23be123c"/><circle cx="200" cy="150" r="7" fill="%237f1d1d"/><text x="200" y="270" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="14" fill="%234b5563">Preset: Severe Pastey Vent &amp; Swelling</text></svg>`;

export default function App() {
  const API_URL = import.meta.env.VITE_API_URL || '';
  
  // Authentication session state
  const [user, setUser] = useState(() => {
    const session = localStorage.getItem('poultry_session');
    return session ? JSON.parse(session) : null;
  });

  // Active subpage
  const [currentPage, setCurrentPage] = useState('dashboard');
  
  // Selected prediction detail item for diagnostic subpage
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);

  // Calibration settings state
  const [settings, setSettings] = useState(() => {
    const savedSettings = localStorage.getItem('poultry_settings');
    if (savedSettings) return JSON.parse(savedSettings);
    return {
      warningThreshold: 50,
      dangerThreshold: 80,
      emailAlerts: true,
      smsAlerts: true,
      pushAlerts: true,
      autoFlagVet: true,
      modelWeight: 'CloacaNet-v2.4-Speed'
    };
  });

  // Screen log database
  const [history, setHistory] = useState(() => {
    const savedHistory = localStorage.getItem('poultry_history');
    if (savedHistory) return JSON.parse(savedHistory);

    // Pre-seed mock data
    const preseededHistory = [
      {
        id: 'CS-739402',
        date: 'Jun 10, 2026',
        time: '09:34 AM',
        image: SVG_HEALTHY,
        imageName: 'baseline_vent_h1.jpg',
        status: 'healthy',
        confidence: 97.4,
        title: 'Normal Healthy Cloaca',
        findings: [
          'Anatomical borders of the cloacal sphincter are clean and well-defined.',
          'No evidence of feather pasting, soil buildup, or fecal accumulation.',
          'Normal mucous membrane color without swelling.'
        ],
        actions: ['Maintain standard farm hygiene and litter status.'],
        reviewed: true,
        flagged: false,
        modelVersion: 'V2.4-CLOACA-NET',
        analysisTime: '1.18s'
      },
      {
        id: 'CS-192840',
        date: 'Jun 12, 2026',
        time: '11:15 AM',
        image: SVG_HEALTHY,
        imageName: 'nest_hen_42.jpg',
        status: 'healthy',
        confidence: 96.1,
        title: 'Normal Healthy Cloaca',
        findings: [
          'Sphincter margins show standard pink color alignment.',
          'Surrounding plumage exhibits dry, clean characteristics.',
          'No abnormal discharges or discharge markings.'
        ],
        actions: ['Maintain standard farm hygiene and litter status.'],
        reviewed: true,
        flagged: false,
        modelVersion: 'V2.4-CLOACA-NET',
        analysisTime: '1.21s'
      },
      {
        id: 'CS-840294',
        date: 'Jun 13, 2026',
        time: '02:40 PM',
        image: SVG_WARNING,
        imageName: 'hen_h4_33.jpg',
        status: 'warning',
        confidence: 68.2,
        title: 'Mild Pasting & Erythema Detected',
        findings: [
          'Moderate feather pasting identified along the lower cloacal margins.',
          'Mild redness (erythema) noted around the sphincter border.'
        ],
        actions: [
          'Isolate subject for detailed physical examination.',
          'Wipe the vent clean with a sanitized warm compress.',
          'Assess flock droppings for evidence of diarrhea.'
        ],
        reviewed: false,
        flagged: true,
        modelVersion: 'V2.4-CLOACA-NET',
        analysisTime: '1.24s'
      },
      {
        id: 'CS-294029',
        date: 'Jun 14, 2026',
        time: '08:50 AM',
        image: SVG_HEALTHY,
        imageName: 'pullet_22b.jpg',
        status: 'healthy',
        confidence: 98.2,
        title: 'Normal Healthy Cloaca',
        findings: ['No abnormalities found. Clean feathers and healthy pink vent.'],
        actions: ['Log as standard healthy baseline.'],
        reviewed: false,
        flagged: false,
        modelVersion: 'V2.4-CLOACA-NET',
        analysisTime: '1.14s'
      },
      {
        id: 'CS-918274',
        date: 'Jun 15, 2026',
        time: '04:12 PM',
        image: SVG_DANGER,
        imageName: 'suspected_salmonella_h4b.jpg',
        status: 'danger',
        confidence: 91.8,
        title: 'Abnormal Vent Discharge (High Salmonella Risk)',
        findings: [
          'Severe pasting of feathers with dense, white fecal discharge.',
          'Pronounced swelling and enlargement of the cloacal opening.',
          'Ulceration or skin erosion visible on the ventral skin border.'
        ],
        actions: [
          'IMMEDIATE ISOLATION: Remove the chicken from the main flock immediately.',
          'QUARANTINE PROTOCOL: Restrict entry to containing house.',
          'ALERT VET: Flag this report to Dr. Robert Carter.',
          'DIAGNOSTIC TEST: Collect fecal swabs for PCR.'
        ],
        reviewed: false,
        flagged: true,
        modelVersion: 'V2.4-CLOACA-NET',
        analysisTime: '1.34s'
      }
    ];

    localStorage.setItem('poultry_history', JSON.stringify(preseededHistory));
    return preseededHistory;
  });

  // Active notifications tray
  const [notifications, setNotifications] = useState(() => {
    const savedNotifs = localStorage.getItem('poultry_notifications');
    if (savedNotifs) return JSON.parse(savedNotifs);

    const initialNotifs = [
      {
        id: 'notif-1',
        title: 'Critical Salmonella Screening Trigger',
        message: 'High-risk vent pasting flagged in Case CS-918274 (House 4B). Vet review requested.',
        type: 'danger',
        time: '2 hours ago',
        read: false
      },
      {
        id: 'notif-2',
        title: 'Veterinary Answer Added',
        message: 'Dr. Robert Carter replied to your question: "Is this chalky build-up normal?".',
        type: 'info',
        time: '1 day ago',
        read: true
      }
    ];
    localStorage.setItem('poultry_notifications', JSON.stringify(initialNotifs));
    return initialNotifs;
  });

  // Toast notifications state
  const [toasts, setToasts] = useState([]);

  // Sync state changes to local storage
  useEffect(() => {
    localStorage.setItem('poultry_history', JSON.stringify(history));
  }, [history]);

  useEffect(() => {
    localStorage.setItem('poultry_notifications', JSON.stringify(notifications));
  }, [notifications]);

  // Load initial database records from FastAPI backend
  useEffect(() => {
    const fetchBackendData = async () => {
      try {
        const histRes = await fetch(`${API_URL}/api/history`);
        if (histRes.ok) {
          const histData = await histRes.json();
          setHistory(histData);
        }
        const notifRes = await fetch(`${API_URL}/api/notifications`);
        if (notifRes.ok) {
          const notifData = await notifRes.json();
          setNotifications(notifData);
        }
      } catch (e) {
        console.error("Failed to connect to Poultry AI backend server", e);
      }
    };
    fetchBackendData();
  }, [API_URL]);

  // Handle user authentication transitions
  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('poultry_session', JSON.stringify(userData));
    setCurrentPage('dashboard');
    showToast('Success', `Logged in successfully as ${userData.name}.`, 'healthy');
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('poultry_session');
    showToast('Signed Out', 'You have been logged out of the session.', 'info');
  };

  const handleUpdateUser = (updatedProfile) => {
    const updatedUser = { ...user, ...updatedProfile };
    setUser(updatedUser);
    localStorage.setItem('poultry_session', JSON.stringify(updatedUser));
  };

  // Toast triggers
  const showToast = (title, desc, type) => {
    const id = `toast-${Date.now()}`;
    setToasts(prev => [...prev, { id, title, desc, type }]);
    
    // Auto-remove after 4.5 seconds
    setTimeout(() => {
      removeToast(id);
    }, 4500);

    // Audio warning siren trigger for critical screens
    if (type === 'danger' && settings.pushAlerts) {
      try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.type = 'sawtooth';
        oscillator.frequency.setValueAtTime(440, audioCtx.currentTime); // A4 note
        oscillator.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.3);
        gainNode.gain.setValueAtTime(0.05, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 0.4);
      } catch (e) {
        console.log("Audio alarm skipped due to browser policy constraint", e);
      }
    }
  };

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  // Notification actions
  const handleClearNotifications = async () => {
    setNotifications([]);
    try {
      await fetch(`${API_URL}/api/notifications/clear`, {
        method: 'DELETE'
      });
    } catch (e) {
      console.error("Failed to clear notifications on backend", e);
    }
  };

  const handleMarkNotificationRead = async (id) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
    try {
      await fetch(`${API_URL}/api/notifications/${id}/read`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ read: true })
      });
    } catch (e) {
      console.error("Failed to mark notification read on backend", e);
    }
  };

  // History action callbacks
  const handleToggleReviewed = async (id) => {
    let nextReviewed = false;
    setHistory(prev => prev.map(item => {
      if (item.id === id) {
        nextReviewed = !item.reviewed;
        showToast(
          'Log Updated', 
          `Case ${id} marked as ${nextReviewed ? 'Reviewed' : 'Pending'}.`, 
          'healthy'
        );
        return { ...item, reviewed: nextReviewed };
      }
      return item;
    }));
    // Sync active detail item if open
    if (selectedHistoryItem && selectedHistoryItem.id === id) {
      setSelectedHistoryItem(prev => ({ ...prev, reviewed: !prev.reviewed }));
    }

    try {
      await fetch(`${API_URL}/api/history/${id}/reviewed`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reviewed: nextReviewed })
      });
    } catch (e) {
      console.error("Failed to sync reviewed status to backend", e);
    }
  };

  const handleToggleFlagged = async (id) => {
    let nextFlagged = false;
    setHistory(prev => prev.map(item => {
      if (item.id === id) {
        nextFlagged = !item.flagged;
        
        // Add support ticket if automated veterinary routing settings is checked
        if (nextFlagged && settings.autoFlagVet) {
          showToast(
            'Veterinarian Alerted', 
            `Case ${id} forwarded directly to Dr. Robert Carter's desk.`, 
            'warning'
          );
        } else {
          showToast(
            'Audit Flag Toggled', 
            `Case ${id} flag status set to ${nextFlagged ? 'Flagged' : 'Normal'}.`, 
            'info'
          );
        }
        
        return { ...item, flagged: nextFlagged };
      }
      return item;
    }));
    // Sync active detail item if open
    if (selectedHistoryItem && selectedHistoryItem.id === id) {
      setSelectedHistoryItem(prev => ({ ...prev, flagged: !prev.flagged }));
    }

    try {
      await fetch(`${API_URL}/api/history/${id}/flagged`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flagged: nextFlagged })
      });
    } catch (e) {
      console.error("Failed to sync flagged status to backend", e);
    }
  };

  const handleRemoveHistoryItem = async (id) => {
    setHistory(prev => prev.filter(item => item.id !== id));
    showToast('Record Deleted', `Log item ${id} was removed from history log database.`, 'info');

    try {
      await fetch(`${API_URL}/api/history/${id}`, {
        method: 'DELETE'
      });
    } catch (e) {
      console.error("Failed to delete prediction from backend", e);
    }
  };

  // Image upload analysis execution callback
  const handleAnalysisComplete = (newResult) => {
    // Save to history list
    setHistory(prev => [newResult, ...prev]);

    // Check thresholds and trigger alerts
    if (newResult.status === 'danger') {
      // Pop toast
      showToast(
        'CRITICAL DETECT ALERT', 
        `Salmonella risk screening positive for case ${newResult.id}. Isolate immediately!`, 
        'danger'
      );
    } else if (newResult.status === 'warning') {
      showToast(
        'WARNING: Pastey Vent', 
        `Mild discoloration/erythema identified in case ${newResult.id}.`, 
        'warning'
      );
    } else {
      showToast(
        'Scan Healthy', 
        `Case ${newResult.id} flagged as healthy baseline (conf: ${newResult.confidence}%).`, 
        'healthy'
      );
    }

    // Reload notifications from backend to capture the alert created by the backend
    const refreshNotifications = async () => {
      try {
        const notifRes = await fetch(`${API_URL}/api/notifications`);
        if (notifRes.ok) {
          const notifData = await notifRes.json();
          setNotifications(notifData);
        }
      } catch (e) {
        console.error(e);
      }
    };
    refreshNotifications();

    // Set active review item
    setSelectedHistoryItem(newResult);
    // Navigate to results screen
    setCurrentPage('analysis');
  };

  const handleCorrection = (correctedResult) => {
    setSelectedHistoryItem(correctedResult);
    setHistory(prev => prev.map(item => item.id === correctedResult.id ? correctedResult : item));
    showToast('AI Re-Calibrated', `Case ${correctedResult.id} corrected to ${correctedResult.title}.`, 'healthy');
  };

  const handleSaveSettings = (updatedSettings) => {
    setSettings(updatedSettings);
    localStorage.setItem('poultry_settings', JSON.stringify(updatedSettings));
    showToast('Settings Saved', 'System sensitivity thresholds updated successfully.', 'healthy');
  };

  // Page switcher router
  const renderActivePage = () => {
    switch (currentPage) {
      case 'dashboard':
        return (
          <Dashboard 
            history={history} 
            setCurrentPage={setCurrentPage} 
            onSelectHistoryItem={setSelectedHistoryItem} 
          />
        );
      case 'upload':
        return (
          <ImageUpload 
            onAnalysisComplete={handleAnalysisComplete}
            settings={settings}
          />
        );
      case 'analysis':
        return (
          <AnalysisResults 
            result={selectedHistoryItem} 
            onBack={() => setCurrentPage(selectedHistoryItem ? 'history' : 'upload')} 
            onToggleReviewed={handleToggleReviewed}
            onToggleFlagged={handleToggleFlagged}
            onCorrect={handleCorrection}
            user={user}
          />
        );
      case 'history':
        return (
          <History 
            history={history} 
            onSelectHistoryItem={setSelectedHistoryItem} 
            setCurrentPage={setCurrentPage} 
            onToggleReviewed={handleToggleReviewed}
            onToggleFlagged={handleToggleFlagged}
            onRemoveItem={handleRemoveHistoryItem}
          />
        );
      case 'community':
        return <Community user={user} />;
      case 'model':
        return <ModelCenter user={user} />;
      case 'settings':
        return (
          <Settings 
            settings={settings} 
            onSaveSettings={handleSaveSettings} 
            user={user}
            onUpdateUser={handleUpdateUser}
          />
        );
      default:
        return (
          <Dashboard 
            history={history} 
            setCurrentPage={setCurrentPage} 
            onSelectHistoryItem={setSelectedHistoryItem} 
          />
        );
    }
  };

  // Render Login/Register form if user session is empty
  if (!user) {
    return (
      <>
        <Auth onLogin={handleLogin} />
        {/* Toast notifications */}
        <div className="toast-container">
          {toasts.map(toast => (
            <div key={toast.id} className={`toast ${toast.type}`}>
              <div className="toast-content">
                <div className="toast-title">{toast.title}</div>
                <div className="toast-desc">{toast.desc}</div>
              </div>
              <button className="toast-close" onClick={() => removeToast(toast.id)}>
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      </>
    );
  }

  // Render normal layout frame
  return (
    <div className="app-container">
      {/* Sidebar navigation */}
      <Sidebar 
        currentPage={currentPage} 
        setCurrentPage={setCurrentPage} 
        user={user} 
        onLogout={handleLogout} 
      />

      {/* Header + Subpage view */}
      <div className="main-content">
        <Header 
          currentPage={currentPage} 
          notifications={notifications}
          onClearNotifications={handleClearNotifications}
          onMarkNotificationRead={handleMarkNotificationRead}
          user={user}
        />
        
        {renderActivePage()}
      </div>

      {/* Toast Overlay Notifications */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast ${toast.type}`}>
            <div className="toast-content">
              <div className="toast-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                {toast.type === 'danger' && <ShieldAlert size={14} className="text-danger" />}
                {toast.type === 'warning' && <AlertTriangle size={14} className="text-warning" />}
                {toast.title}
              </div>
              <div className="toast-desc">{toast.desc}</div>
            </div>
            <button className="toast-close" onClick={() => removeToast(toast.id)}>
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
