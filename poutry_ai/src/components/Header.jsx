import React, { useState, useRef, useEffect } from 'react';
import { Bell, Menu, ShieldAlert, CheckCircle, HelpCircle } from 'lucide-react';

export default function Header({ 
  currentPage, 
  notifications, 
  onClearNotifications, 
  onMarkNotificationRead,
  user 
}) {
  const [showNotifications, setShowNotifications] = useState(false);
  const dropdownRef = useRef(null);
  
  const unreadCount = notifications.filter(n => !n.read).length;

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getPageTitle = () => {
    switch (currentPage) {
      case 'dashboard':
        return 'Analytics Dashboard';
      case 'upload':
        return 'Salmonella Risk Upload';
      case 'analysis':
        return 'AI Diagnostic Report';
      case 'history':
        return 'Prediction History Logs';
      case 'community':
        return 'Community & Expert Support';
      case 'settings':
        return 'System Settings';
      default:
        return 'CloacaScan AI';
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'danger':
        return <ShieldAlert className="text-danger" size={16} />;
      case 'healthy':
        return <CheckCircle className="text-healthy" size={16} />;
      default:
        return <HelpCircle className="text-warning" size={16} />;
    }
  };

  return (
    <header className="header">
      <div className="header-title-container">
        <button className="menu-toggle">
          <Menu size={24} />
        </button>
        <h1 className="header-title">{getPageTitle()}</h1>
      </div>

      <div className="header-actions">
        <div className="notification-bell-container" ref={dropdownRef}>
          <button 
            className="notification-btn" 
            onClick={() => setShowNotifications(!showNotifications)}
            aria-label="View notifications"
          >
            <Bell size={20} />
            {unreadCount > 0 && <span className="notification-badge" />}
          </button>

          {showNotifications && (
            <div className="notification-dropdown">
              <div className="notification-dropdown-header">
                <span>Alert Notifications</span>
                {unreadCount > 0 && (
                  <button 
                    className="notification-dropdown-clear"
                    onClick={() => {
                      onClearNotifications();
                      setShowNotifications(false);
                    }}
                  >
                    Clear all
                  </button>
                )}
              </div>
              <div className="notification-list">
                {notifications.length === 0 ? (
                  <div className="notification-empty">
                    No recent notifications
                  </div>
                ) : (
                  notifications.map((notif) => (
                    <div 
                      key={notif.id} 
                      className={`notification-item ${!notif.read ? 'unread' : ''}`}
                      onClick={() => {
                        onMarkNotificationRead(notif.id);
                        setShowNotifications(false);
                      }}
                    >
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                        <div style={{ marginTop: '2px' }}>
                          {getNotificationIcon(notif.type)}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div className="notification-item-title">{notif.title}</div>
                          <div className="notification-item-desc">{notif.message}</div>
                          <div className="notification-item-time">{notif.time}</div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {user && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', fontSize: '13px' }}>
            <span style={{ fontWeight: 600 }}>{user.name}</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: '11px', textTransform: 'capitalize' }}>
              {user.farmName} • {user.role}
            </span>
          </div>
        )}
      </div>
    </header>
  );
}
