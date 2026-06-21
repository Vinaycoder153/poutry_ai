import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  ShieldCheck, 
  BellRing, 
  ArrowUpRight, 
  ArrowDownRight, 
  Upload, 
  LifeBuoy, 
  Sliders,
  ChevronRight
} from 'lucide-react';

export default function Dashboard({ history, setCurrentPage, onSelectHistoryItem }) {
  const [timeRange, setTimeRange] = useState('7D');
  const [stats, setStats] = useState({
    total: 0,
    suspected: 0,
    healthy: 0,
    flagged: 0,
    healthyRate: 0,
    totalTrend: 12.5,
    suspectedTrend: -4.2,
    healthyRateTrend: 1.8,
    flaggedTrend: 0
  });

  useEffect(() => {
    // Calculate stats based on history and time range
    const now = new Date();
    let filteredHistory = [...history];

    if (timeRange === 'Today') {
      const todayStr = now.toDateString();
      filteredHistory = history.filter(item => new Date(item.date).toDateString() === todayStr);
    } else if (timeRange === '7D') {
      const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      filteredHistory = history.filter(item => new Date(item.date) >= sevenDaysAgo);
    } else if (timeRange === '30D') {
      const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      filteredHistory = history.filter(item => new Date(item.date) >= thirtyDaysAgo);
    }

    const total = filteredHistory.length;
    const suspected = filteredHistory.filter(item => item.status === 'danger' || item.status === 'warning').length;
    const healthy = filteredHistory.filter(item => item.status === 'healthy').length;
    const flagged = filteredHistory.filter(item => item.flagged && !item.reviewed).length;
    const healthyRate = total > 0 ? Math.round((healthy / total) * 100) : 100;

    // Static trends just for visual fidelity
    let totalTrend = 12.5;
    let suspectedTrend = -4.2;
    let healthyRateTrend = 1.8;

    if (timeRange === 'Today') {
      totalTrend = 5.2;
      suspectedTrend = 0;
      healthyRateTrend = 0.5;
    } else if (timeRange === '30D') {
      totalTrend = 24.8;
      suspectedTrend = -8.5;
      healthyRateTrend = 3.2;
    }

    setStats({
      total,
      suspected,
      healthy,
      flagged,
      healthyRate,
      totalTrend,
      suspectedTrend,
      healthyRateTrend,
      flaggedTrend: flagged > 0 ? 1 : 0
    });
  }, [history, timeRange]);

  const recentAlerts = history
    .filter(item => item.status === 'danger' || item.status === 'warning')
    .slice(0, 4);

  // Generate coordinates for SVG Sparkline chart
  // Shows simulated Salmonella detection trend
  const getChartPoints = () => {
    // Generate 7 points
    const points = [12, 18, 15, 22, 10, 8, stats.suspected * 1.5 + 4];
    const maxVal = Math.max(...points, 25);
    const minVal = 0;
    const width = 500;
    const height = 180;
    const padding = 15;
    
    const xStep = (width - padding * 2) / (points.length - 1);
    
    return points.map((p, i) => {
      const x = padding + i * xStep;
      // invert Y axis
      const y = height - padding - ((p - minVal) / (maxVal - minVal)) * (height - padding * 2);
      return { x, y, val: p };
    });
  };

  const chartPoints = getChartPoints();
  const sparklinePath = chartPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

  // Direct mock data for Salmonella vs Healthy daily screening counts
  const barChartData = [
    { label: 'Mon', healthy: 24, suspected: 2 },
    { label: 'Tue', healthy: 32, suspected: 4 },
    { label: 'Wed', healthy: 28, suspected: 1 },
    { label: 'Thu', healthy: 38, suspected: 5 },
    { label: 'Fri', healthy: 45, suspected: 3 },
    { label: 'Sat', healthy: 20, suspected: 0 },
    { label: 'Sun', healthy: stats.healthy || 18, suspected: stats.suspected || 2 },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 700 }}>Flock Screening Command Center</h2>
          <p className="page-desc">Real-time cloacal/vent status screening & Salmonella hazard indicators</p>
        </div>
        <div style={{
          display: 'flex',
          backgroundColor: 'var(--bg-primary)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '4px',
          boxShadow: 'var(--shadow-sm)'
        }}>
          {['Today', '7D', '30D'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              style={{
                border: 'none',
                backgroundColor: timeRange === range ? 'var(--primary-color)' : 'transparent',
                color: timeRange === range ? 'white' : 'var(--text-secondary)',
                padding: '6px 16px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '13px',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all var(--transition-fast)'
              }}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="dashboard-grid">
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Total Vents Screened</span>
            <div className="kpi-icon-container blue">
              <Activity size={18} />
            </div>
          </div>
          <div className="kpi-value">{stats.total}</div>
          <div className={`kpi-trend ${stats.totalTrend >= 0 ? 'up' : 'down'}`}>
            {stats.totalTrend >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            <span>{Math.abs(stats.totalTrend)}%</span>
            <span className="kpi-trend-label">vs last period</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Suspected Risk Cases</span>
            <div className="kpi-icon-container red">
              <AlertTriangle size={18} />
            </div>
          </div>
          <div className="kpi-value">{stats.suspected}</div>
          <div className={`kpi-trend ${stats.suspectedTrend <= 0 ? 'up' : 'down'}`}>
            {stats.suspectedTrend <= 0 ? <ArrowDownRight size={14} /> : <ArrowUpRight size={14} />}
            <span style={{ color: stats.suspectedTrend <= 0 ? 'var(--healthy-color)' : 'var(--danger-color)' }}>
              {Math.abs(stats.suspectedTrend)}%
            </span>
            <span className="kpi-trend-label">vs last period</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Healthy Vent Ratio</span>
            <div className="kpi-icon-container green">
              <ShieldCheck size={18} />
            </div>
          </div>
          <div className="kpi-value">{stats.healthyRate}%</div>
          <div className={`kpi-trend ${stats.healthyRateTrend >= 0 ? 'up' : 'down'}`}>
            {stats.healthyRateTrend >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            <span>{Math.abs(stats.healthyRateTrend)}%</span>
            <span className="kpi-trend-label">vs last period</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Open Vet Alerts</span>
            <div className="kpi-icon-container amber">
              <BellRing size={18} />
            </div>
          </div>
          <div className="kpi-value">{stats.flagged}</div>
          <div className="kpi-trend up" style={{ color: stats.flagged > 0 ? 'var(--warning-color)' : 'var(--healthy-color)' }}>
            <span>{stats.flagged > 0 ? 'Requires attention' : 'All clear'}</span>
          </div>
        </div>
      </div>

      {/* Main dashboard body: charts on left, lists/shortcuts on right */}
      <div className="dashboard-panels">
        {/* Left Side: Analytics & Charts */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Trend Chart (Line) */}
          <div className="panel">
            <div className="panel-header">
              <h3 className="panel-title">Suspected Salmonella Risk Detections (Trend)</h3>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Daily Suspected Cases Count</span>
            </div>
            
            <div style={{ position: 'relative', height: '200px', width: '100%', paddingLeft: '30px', paddingBottom: '20px' }}>
              {/* Y Axis line */}
              <div style={{
                position: 'absolute',
                left: '25px',
                top: 0,
                bottom: '20px',
                borderLeft: '1px solid var(--border-color)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                fontSize: '10px',
                color: 'var(--text-tertiary)',
                textAlign: 'right',
                paddingRight: '6px'
              }}>
                <span>25</span>
                <span>15</span>
                <span>5</span>
                <span>0</span>
              </div>

              {/* SVG Sparkline */}
              <svg style={{ width: '100%', height: '180px', overflow: 'visible' }} viewBox="0 0 500 180" preserveAspectRatio="none">
                {/* Horizontal grid lines */}
                <line x1="0" y1="15" x2="500" y2="15" stroke="var(--bg-tertiary)" strokeWidth="1" strokeDasharray="4 4" />
                <line x1="0" y1="80" x2="500" y2="80" stroke="var(--bg-tertiary)" strokeWidth="1" strokeDasharray="4 4" />
                <line x1="0" y1="145" x2="500" y2="145" stroke="var(--bg-tertiary)" strokeWidth="1" strokeDasharray="4 4" />
                
                {/* Gradient Fill under sparkline */}
                <defs>
                  <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--danger-color)" stopOpacity="0.15" />
                    <stop offset="100%" stopColor="var(--danger-color)" stopOpacity="0.0" />
                  </linearGradient>
                </defs>
                <path 
                  d={`${sparklinePath} L ${chartPoints[chartPoints.length-1].x} 165 L ${chartPoints[0].x} 165 Z`} 
                  fill="url(#chartGradient)" 
                />

                {/* Line Path */}
                <path 
                  d={sparklinePath} 
                  fill="none" 
                  stroke="var(--danger-color)" 
                  strokeWidth="2.5" 
                  strokeLinecap="round"
                />

                {/* Data Points */}
                {chartPoints.map((p, i) => (
                  <g key={i}>
                    <circle 
                      cx={p.x} 
                      cy={p.y} 
                      r="4" 
                      fill="white" 
                      stroke="var(--danger-color)" 
                      strokeWidth="2" 
                    />
                    <circle 
                      cx={p.x} 
                      cy={p.y} 
                      r="9" 
                      fill="var(--danger-color)" 
                      fillOpacity="0.0"
                      style={{ cursor: 'pointer' }}
                    >
                      <title>Day {i+1}: {p.val} suspected cases</title>
                    </circle>
                  </g>
                ))}
              </svg>

              {/* X Axis labels */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                paddingLeft: '15px',
                paddingRight: '15px',
                fontSize: '11px',
                color: 'var(--text-secondary)',
                marginTop: '6px'
              }}>
                <span>Mon</span>
                <span>Tue</span>
                <span>Wed</span>
                <span>Thu</span>
                <span>Fri</span>
                <span>Sat</span>
                <span>Sun (Today)</span>
              </div>
            </div>
          </div>

          {/* Bar Chart (Daily Screening Volume) */}
          <div className="panel">
            <div className="panel-header">
              <h3 className="panel-title">Daily Screening Statistics</h3>
              <div className="chart-legend">
                <div className="legend-item">
                  <div className="legend-color healthy"></div>
                  <span>Healthy</span>
                </div>
                <div className="legend-item">
                  <div className="legend-color suspected"></div>
                  <span>Suspected Salmonella</span>
                </div>
              </div>
            </div>

            <div className="chart-container">
              <div className="chart-axis-y">
                <span>50</span>
                <span>30</span>
                <span>10</span>
                <span>0</span>
              </div>
              
              <div className="chart-bars-wrapper">
                {barChartData.map((d, i) => {
                  const maxTotal = 50;
                  const healthyHeight = Math.min((d.healthy / maxTotal) * 200, 200);
                  const suspectedHeight = Math.min((d.suspected / maxTotal) * 200, 200);
                  
                  return (
                    <div key={i} className="chart-bar-group">
                      <div style={{ display: 'flex', gap: '4px', alignItems: 'flex-end', height: '200px' }}>
                        {/* Healthy bar */}
                        <div 
                          className="chart-bar-container" 
                          style={{ height: '200px', width: '14px' }}
                        >
                          <div 
                            className="chart-bar-fill healthy" 
                            style={{ height: `${healthyHeight}px` }}
                          />
                          <div className="chart-bar-hover-val">{d.healthy} Healthy</div>
                        </div>

                        {/* Suspected bar */}
                        <div 
                          className="chart-bar-container" 
                          style={{ height: '200px', width: '14px' }}
                        >
                          <div 
                            className="chart-bar-fill suspected" 
                            style={{ height: `${suspectedHeight}px` }}
                          />
                          <div className="chart-bar-hover-val" style={{ background: 'var(--danger-color)' }}>
                            {d.suspected} Risk
                          </div>
                        </div>
                      </div>
                      <span className="chart-bar-label">{d.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

        </div>

        {/* Right Side: Alerts, Quick Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Quick Actions Panel */}
          <div className="panel">
            <h3 className="panel-title" style={{ marginBottom: '16px' }}>Operator Actions</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button 
                onClick={() => setCurrentPage('upload')} 
                className="btn btn-primary btn-block" 
                style={{ padding: '12px' }}
              >
                <Upload size={18} />
                Scan Chicken Vent
              </button>
              <button 
                onClick={() => setCurrentPage('community')} 
                className="btn btn-outline btn-block" 
                style={{ padding: '12px' }}
              >
                <LifeBuoy size={18} />
                Vet Consult Desk
              </button>
              <button 
                onClick={() => setCurrentPage('settings')} 
                className="btn btn-secondary btn-block" 
                style={{ padding: '12px', justifyContent: 'center' }}
              >
                <Sliders size={18} />
                Change Thresholds
              </button>
            </div>
          </div>

          {/* Recent Alerts List */}
          <div className="panel">
            <div className="panel-header">
              <h3 className="panel-title">Active Health Warnings</h3>
              <span 
                onClick={() => setCurrentPage('history')} 
                style={{ fontSize: '12px', color: 'var(--primary-color)', cursor: 'pointer', fontWeight: 500 }}
              >
                View Logs
              </span>
            </div>
            
            {recentAlerts.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '32px 16px',
                color: 'var(--text-secondary)',
                fontSize: '13px'
              }}>
                No warnings detected in this time range. Flock is stable.
              </div>
            ) : (
              <div className="recent-alerts-list">
                {recentAlerts.map((item) => (
                  <div 
                    key={item.id} 
                    className="alert-item-card"
                    style={{ borderLeft: `3px solid ${item.status === 'danger' ? 'var(--danger-color)' : 'var(--warning-color)'}` }}
                  >
                    <div className="alert-item-info">
                      <img 
                        src={item.image} 
                        alt={item.id} 
                        className="alert-item-thumb" 
                      />
                      <div className="alert-item-details">
                        <span className="alert-item-title-text">
                          ID: {item.id}
                        </span>
                        <div className="alert-item-meta">
                          <span>Conf: {item.confidence}%</span>
                          <span>{item.date}</span>
                        </div>
                      </div>
                    </div>
                    
                    <button 
                      onClick={() => {
                        onSelectHistoryItem(item);
                        setCurrentPage('analysis');
                      }}
                      className="btn btn-outline"
                      style={{ padding: '4px 8px', borderRadius: 'var(--radius-sm)', fontSize: '11px', display: 'flex', gap: '2px', alignItems: 'center' }}
                    >
                      Report
                      <ChevronRight size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
