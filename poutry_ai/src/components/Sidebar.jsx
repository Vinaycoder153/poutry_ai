import { 
  LayoutDashboard, 
  UploadCloud, 
  History, 
  Users, 
  Settings, 
  LogOut, 
  Activity,
  Cpu
} from 'lucide-react';

export default function Sidebar({ currentPage, setCurrentPage, user, onLogout }) {
  const navItems = [
    { id: 'dashboard', name: 'Dashboard', icon: LayoutDashboard },
    { id: 'upload', name: 'Image Upload', icon: UploadCloud },
    { id: 'history', name: 'Prediction History', icon: History },
    { id: 'model', name: 'AI Model Center', icon: Cpu },
    { id: 'community', name: 'Community Support', icon: Users },
    { id: 'settings', name: 'Settings', icon: Settings },
  ];

  const getInitials = (name) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map((n) => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <Activity size={24} strokeWidth={2.5} />
          </div>
          <span className="sidebar-logo-text">CloacaScan AI</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id || (item.id === 'upload' && currentPage === 'analysis');
          return (
            <div
              key={item.id}
              onClick={() => setCurrentPage(item.id)}
              className={`sidebar-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={20} />
              <span>{item.name}</span>
            </div>
          );
        })}
      </nav>

      {user && (
        <div className="sidebar-footer">
          <div className="user-profile-summary">
            <div className="user-avatar">
              {getInitials(user.name)}
            </div>
            <div className="user-info">
              <span className="user-name">{user.name}</span>
              <span className="user-role">{user.role === 'veterinarian' ? 'Attending Vet' : 'Farm Operator'}</span>
            </div>
          </div>
          <button onClick={onLogout} className="logout-btn">
            <LogOut size={18} />
            <span>Sign Out</span>
          </button>
        </div>
      )}
    </aside>
  );
}
