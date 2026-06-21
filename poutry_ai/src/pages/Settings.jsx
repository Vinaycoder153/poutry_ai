import React, { useState } from 'react';
import { 
  Sliders, 
  Bell, 
  User, 
  SlidersHorizontal, 
  CheckCircle, 
  Save,
  Database
} from 'lucide-react';

export default function Settings({ 
  settings, 
  onSaveSettings, 
  user, 
  onUpdateUser 
}) {
  // Threshold sliders state
  const [warningThreshold, setWarningThreshold] = useState(settings.warningThreshold || 50);
  const [dangerThreshold, setDangerThreshold] = useState(settings.dangerThreshold || 80);

  // Profile state
  const [profileName, setProfileName] = useState(user ? user.name : '');
  const [profileEmail, setProfileEmail] = useState(user ? user.email : '');
  const [profileFarm, setProfileFarm] = useState(user ? user.farmName : '');
  const [profileRole, setProfileRole] = useState(user ? user.role : 'operator');

  // Preferences checkboxes state
  const [emailAlerts, setEmailAlerts] = useState(settings.emailAlerts !== false);
  const [smsAlerts, setSmsAlerts] = useState(settings.smsAlerts !== false);
  const [pushAlerts, setPushAlerts] = useState(settings.pushAlerts !== false);
  const [autoFlagVet, setAutoFlagVet] = useState(settings.autoFlagVet !== false);

  // Model selection state
  const [modelWeight, setModelWeight] = useState(settings.modelWeight || 'CloacaNet-v2.4-Speed');

  // Status feedback
  const [showSuccess, setShowSuccess] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();

    // Update settings parent state
    onSaveSettings({
      warningThreshold,
      dangerThreshold,
      emailAlerts,
      smsAlerts,
      pushAlerts,
      autoFlagVet,
      modelWeight
    });

    // Update user profile in parent state
    onUpdateUser({
      name: profileName,
      email: profileEmail,
      farmName: profileFarm,
      role: profileRole
    });

    setShowSuccess(true);
    setTimeout(() => {
      setShowSuccess(false);
    }, 3000);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 700 }}>System Control &amp; Settings</h2>
          <p className="page-desc">Adjust AI detection warning limits, configure biosecurity alerts, and update operator profiles</p>
        </div>
      </div>

      {showSuccess && (
        <div style={{
          display: 'flex',
          gap: '8px',
          alignItems: 'center',
          backgroundColor: 'var(--healthy-light)',
          color: 'var(--healthy-color)',
          border: '1px solid var(--healthy-border)',
          borderRadius: 'var(--radius-sm)',
          padding: '12px 16px',
          fontSize: '14px',
          marginBottom: '24px'
        }}>
          <CheckCircle size={18} />
          <span>Settings successfully saved and synced to database storage.</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="settings-grid">
          
          {/* Left panel: Thresholds and notifications */}
          <div className="settings-section">
            
            {/* Calibration Slider Panel */}
            <div className="panel">
              <h3 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <SlidersHorizontal size={18} className="text-primary" style={{ color: 'var(--primary-color)' }} />
                AI Calibration Thresholds
              </h3>
              
              <div className="slider-group">
                <div className="slider-labels">
                  <span style={{ fontWeight: 600 }}>Warning Alert Level Sensitivity</span>
                  <span style={{ color: 'var(--warning-color)', fontWeight: 700 }}>{warningThreshold}% Confidence</span>
                </div>
                <input 
                  type="range" 
                  min="30" 
                  max="65" 
                  className="slider-input" 
                  value={warningThreshold}
                  onChange={(e) => setWarningThreshold(parseInt(e.target.value))}
                />
                <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Triggers Amber warning markers for minor pasted feathers or mild erythema when confidence exceeds this limit.
                </p>
              </div>

              <div className="slider-group" style={{ marginTop: '20px' }}>
                <div className="slider-labels">
                  <span style={{ fontWeight: 600 }}>Critical Danger (Salmonella Risk) Threshold</span>
                  <span style={{ color: 'var(--danger-color)', fontWeight: 700 }}>{dangerThreshold}% Confidence</span>
                </div>
                <input 
                  type="range" 
                  min="70" 
                  max="95" 
                  className="slider-input" 
                  value={dangerThreshold}
                  onChange={(e) => setDangerThreshold(parseInt(e.target.value))}
                />
                <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Triggers Red biosecurity danger flags, push alarm tones, and queues immediate isolation checksheets.
                </p>
              </div>
            </div>

            {/* Notification alert channels */}
            <div className="panel">
              <h3 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Bell size={18} className="text-primary" style={{ color: 'var(--primary-color)' }} />
                Biosecurity Alert Preferences
              </h3>

              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input 
                    type="checkbox" 
                    checked={emailAlerts}
                    onChange={(e) => setEmailAlerts(e.target.checked)}
                  />
                  <div>
                    <span style={{ fontWeight: 500, display: 'block', color: 'var(--text-primary)' }}>Email Incident Summary</span>
                    <span style={{ fontSize: '12px' }}>Email complete PDF reports automatically to the lab when critical danger triggers.</span>
                  </div>
                </label>

                <label className="checkbox-label" style={{ marginTop: '6px' }}>
                  <input 
                    type="checkbox" 
                    checked={smsAlerts}
                    onChange={(e) => setSmsAlerts(e.target.checked)}
                  />
                  <div>
                    <span style={{ fontWeight: 500, display: 'block', color: 'var(--text-primary)' }}>Critical SMS Alerts</span>
                    <span style={{ fontSize: '12px' }}>Send urgent text notification warnings to caretakers and vets on high-risk detections.</span>
                  </div>
                </label>

                <label className="checkbox-label" style={{ marginTop: '6px' }}>
                  <input 
                    type="checkbox" 
                    checked={pushAlerts}
                    onChange={(e) => setPushAlerts(e.target.checked)}
                  />
                  <div>
                    <span style={{ fontWeight: 500, display: 'block', color: 'var(--text-primary)' }}>In-App Sound Alarms</span>
                    <span style={{ fontSize: '12px' }}>Play an audible warning siren inside the browser window on critical screens.</span>
                  </div>
                </label>

                <label className="checkbox-label" style={{ marginTop: '6px' }}>
                  <input 
                    type="checkbox" 
                    checked={autoFlagVet}
                    onChange={(e) => setAutoFlagVet(e.target.checked)}
                  />
                  <div>
                    <span style={{ fontWeight: 500, display: 'block', color: 'var(--text-primary)' }}>Automatic Veterinary Routing</span>
                    <span style={{ fontSize: '12px' }}>Instantly flag and forward severe detections directly to Dr. Carter's Q&amp;A support desk.</span>
                  </div>
                </label>
              </div>
            </div>

          </div>

          {/* Right panel: User Profile & model options */}
          <div className="settings-section">
            
            {/* Operator Profile details */}
            <div className="panel">
              <h3 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <User size={18} className="text-primary" style={{ color: 'var(--primary-color)' }} />
                Operator Profile
              </h3>

              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  type="email"
                  className="form-input"
                  value={profileEmail}
                  onChange={(e) => setProfileEmail(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Farm / Hatchery Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={profileFarm}
                  onChange={(e) => setProfileFarm(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Role Classification</label>
                <select
                  className="form-select"
                  value={profileRole}
                  onChange={(e) => setProfileRole(e.target.value)}
                >
                  <option value="operator">Farm Operator / Caretaker</option>
                  <option value="veterinarian">Attending Veterinarian</option>
                </select>
              </div>
            </div>

            {/* Neural Net Weights Profile */}
            <div className="panel">
              <h3 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Database size={18} className="text-primary" style={{ color: 'var(--primary-color)' }} />
                AI Inference Engine Weight
              </h3>

              <div className="form-group">
                <label className="form-label">Model Version Weights</label>
                <select
                  className="form-select"
                  value={modelWeight}
                  onChange={(e) => setModelWeight(e.target.value)}
                >
                  <option value="CloacaNet-v2.4-Speed">CloacaNet-v2.4-Speed (1.2s inference, mobile-optimized)</option>
                  <option value="CloacaNet-v3.0-Accurate">CloacaNet-v3.0-Accurate (2.4s inference, high resolution - Beta)</option>
                  <option value="CloacaNet-v1.8-Legacy">CloacaNet-v1.8-Legacy (Standard classification, stable)</option>
                </select>
              </div>
              <p style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                V3.0 incorporates advanced multi-spectral analysis parameters targeting microscopic yolk-sac infections, currently under field trials.
              </p>
            </div>

            <button type="submit" className="btn btn-primary btn-block" style={{ padding: '12px', fontSize: '15px' }}>
              <Save size={16} />
              Save Settings &amp; Profile Updates
            </button>

          </div>

        </div>
      </form>
    </div>
  );
}
