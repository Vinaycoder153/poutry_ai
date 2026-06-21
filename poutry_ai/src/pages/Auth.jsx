import React, { useState } from 'react';
import { Activity, ShieldAlert, CheckCircle2 } from 'lucide-react';

export default function Auth({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [farmName, setFarmName] = useState('');
  const [role, setRole] = useState('operator');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Pre-seed some mock users in localStorage if they don't exist
  const getRegisteredUsers = () => {
    const users = localStorage.getItem('poultry_users');
    if (!users) {
      const defaultUsers = [
        {
          name: 'Sarah Jenkins',
          email: 'operator@farm.com',
          password: 'operator123',
          farmName: 'Emerald Fields Farm',
          role: 'operator'
        },
        {
          name: 'Dr. Robert Carter',
          email: 'vet@farm.com',
          password: 'vet123',
          farmName: 'Poultry Health Partners',
          role: 'veterinarian'
        }
      ];
      localStorage.setItem('poultry_users', JSON.stringify(defaultUsers));
      return defaultUsers;
    }
    return JSON.parse(users);
  };

  const handleLogin = (e) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please fill in all fields.');
      return;
    }

    const users = getRegisteredUsers();
    const user = users.find(u => u.email.toLowerCase() === email.toLowerCase() && u.password === password);

    if (user) {
      onLogin(user);
    } else {
      setError('Invalid email or password. Try using operator@farm.com (pwd: operator123) or vet@farm.com (pwd: vet123) for testing.');
    }
  };

  const handleRegister = (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!name || !farmName || !email || !password) {
      setError('Please fill in all fields.');
      return;
    }

    const users = getRegisteredUsers();
    if (users.find(u => u.email.toLowerCase() === email.toLowerCase())) {
      setError('This email is already registered.');
      return;
    }

    const newUser = { name, farmName, email, password, role };
    const updatedUsers = [...users, newUser];
    localStorage.setItem('poultry_users', JSON.stringify(updatedUsers));

    setSuccess('Registration successful! You can now log in.');
    // Switch to login tab and fill email
    setTimeout(() => {
      setIsRegister(false);
      setEmail(email);
      setPassword('');
      setSuccess('');
    }, 1500);
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-background-decoration top-right"></div>
      <div className="auth-background-decoration bottom-left"></div>

      <div className="auth-card">
        <div className="auth-logo">
          <Activity size={32} className="text-primary" style={{ color: 'var(--primary-color)' }} />
          <span className="auth-logo-text">CloacaScan AI</span>
        </div>

        <h2 className="auth-title">{isRegister ? 'Create Account' : 'Welcome Back'}</h2>
        <p className="auth-subtitle">
          {isRegister 
            ? 'Sign up to screen poultry vents and manage Salmonella risks' 
            : 'Login to monitor flock health and check diagnostic reports'}
        </p>

        {error && (
          <div style={{
            display: 'flex',
            gap: '8px',
            alignItems: 'center',
            backgroundColor: 'var(--danger-light)',
            color: 'var(--danger-color)',
            border: '1px solid var(--danger-border)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 14px',
            fontSize: '13px',
            marginBottom: '20px'
          }}>
            <ShieldAlert size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div style={{
            display: 'flex',
            gap: '8px',
            alignItems: 'center',
            backgroundColor: 'var(--healthy-light)',
            color: 'var(--healthy-color)',
            border: '1px solid var(--healthy-border)',
            borderRadius: 'var(--radius-sm)',
            padding: '10px 14px',
            fontSize: '13px',
            marginBottom: '20px'
          }}>
            <CheckCircle2 size={18} style={{ flexShrink: 0 }} />
            <span>{success}</span>
          </div>
        )}

        {isRegister ? (
          <form onSubmit={handleRegister}>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Sarah Jenkins"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Farm / Organization Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Emerald Fields Farm"
                value={farmName}
                onChange={(e) => setFarmName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Your Role</label>
              <select
                className="form-select"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="operator">Farm Operator / Caretaker</option>
                <option value="veterinarian">Attending Veterinarian</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-input"
                placeholder="operator@farm.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button type="submit" className="btn btn-primary btn-block">
              Register Account
            </button>
          </form>
        ) : (
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-input"
                placeholder="operator@farm.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button type="submit" className="btn btn-primary btn-block">
              Sign In
            </button>
          </form>
        )}

        <div className="auth-footer">
          {isRegister ? (
            <span>
              Already have an account?{' '}
              <button 
                onClick={() => {
                  setIsRegister(false);
                  setError('');
                  setSuccess('');
                }} 
                className="auth-link"
                style={{ background: 'none', border: 'none', cursor: 'pointer' }}
              >
                Sign In
              </button>
            </span>
          ) : (
            <span>
              Don't have an account?{' '}
              <button 
                onClick={() => {
                  setIsRegister(true);
                  setError('');
                  setSuccess('');
                }} 
                className="auth-link"
                style={{ background: 'none', border: 'none', cursor: 'pointer' }}
              >
                Register
              </button>
            </span>
          )}
        </div>

        {!isRegister && (
          <div style={{
            marginTop: '24px',
            padding: '12px',
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            fontSize: '11px',
            color: 'var(--text-secondary)'
          }}>
            <strong style={{ display: 'block', marginBottom: '4px', color: 'var(--text-primary)' }}>
              Demo Access Credentials:
            </strong>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <div>• <strong>Operator</strong>: operator@farm.com / operator123</div>
              <div>• <strong>Veterinarian</strong>: vet@farm.com / vet123</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
