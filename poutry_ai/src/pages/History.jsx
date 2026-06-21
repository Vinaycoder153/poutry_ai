import React, { useState } from 'react';
import { 
  Search, 
  Download, 
  Trash2, 
  Check, 
  Flag, 
  ExternalLink,
  Filter,
  CheckSquare
} from 'lucide-react';

export default function History({ 
  history, 
  onSelectHistoryItem, 
  setCurrentPage,
  onToggleReviewed,
  onToggleFlagged,
  onRemoveItem
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [flagFilter, setFlagFilter] = useState('all');

  const filteredHistory = history.filter(item => {
    // Search filter
    const matchesSearch = item.id.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          (item.imageName && item.imageName.toLowerCase().includes(searchTerm.toLowerCase()));

    // Status filter
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;

    // Flag/Review filter
    let matchesFlag = true;
    if (flagFilter === 'flagged') {
      matchesFlag = item.flagged;
    } else if (flagFilter === 'reviewed') {
      matchesFlag = item.reviewed;
    } else if (flagFilter === 'pending') {
      matchesFlag = !item.reviewed && !item.flagged;
    }

    return matchesSearch && matchesStatus && matchesFlag;
  });

  const exportCSV = () => {
    if (filteredHistory.length === 0) return;

    const headers = ['Case ID', 'Date', 'Time', 'Image Name', 'Status', 'Confidence %', 'Reviewed', 'Flagged', 'Model Version', 'Analysis Time'];
    const rows = filteredHistory.map(item => [
      item.id,
      item.date,
      item.time,
      item.imageName || 'N/A',
      item.status.toUpperCase(),
      item.confidence,
      item.reviewed ? 'YES' : 'NO',
      item.flagged ? 'YES' : 'NO',
      item.modelVersion,
      item.analysisTime
    ]);

    const csvContent = "data:text/csv;charset=utf-8," 
      + [headers.join(','), ...rows.map(e => e.map(val => `"${val}"`).join(','))].join('\n');
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `CloacaScan_Export_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleRowClick = (item) => {
    onSelectHistoryItem(item);
    setCurrentPage('analysis');
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 700 }}>Prediction &amp; Diagnostic Logs</h2>
          <p className="page-desc">Search, filter, review, and export past AI cloacal health screening evaluations</p>
        </div>
        
        <button 
          onClick={exportCSV} 
          disabled={filteredHistory.length === 0}
          className="btn btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <Download size={16} />
          Export CSV Log
        </button>
      </div>

      {/* Filter controls panel */}
      <div className="panel" style={{ marginBottom: '24px', padding: '16px' }}>
        <div className="history-controls">
          
          {/* Search */}
          <div className="search-input-wrapper">
            <Search size={18} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search by Case ID or filename..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Status Select */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Filter size={14} style={{ color: 'var(--text-secondary)' }} />
            <select
              className="filter-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Risk Levels</option>
              <option value="healthy">Healthy Only</option>
              <option value="warning">Warning Only</option>
              <option value="danger">High Risk Only</option>
            </select>
          </div>

          {/* Audit Flag Select */}
          <div>
            <select
              className="filter-select"
              value={flagFilter}
              onChange={(e) => setFlagFilter(e.target.value)}
            >
              <option value="all">All Audit Statuses</option>
              <option value="pending">Pending Review</option>
              <option value="reviewed">Reviewed Logs</option>
              <option value="flagged">Flagged Cases</option>
            </select>
          </div>

        </div>
      </div>

      {/* Predictions Table */}
      {filteredHistory.length === 0 ? (
        <div className="panel" style={{ textAlign: 'center', padding: '48px 24px' }}>
          <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
            No prediction logs matched your active search filters.
          </span>
        </div>
      ) : (
        <div className="table-container">
          <table className="history-table">
            <thead>
              <tr>
                <th style={{ width: '60px' }}>Thumb</th>
                <th>Case ID</th>
                <th>Timestamp</th>
                <th>File / Source</th>
                <th>Risk Level</th>
                <th>Confidence</th>
                <th>Vet Audits</th>
                <th style={{ textAlign: 'center', width: '150px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredHistory.map((item) => (
                <tr key={item.id}>
                  {/* Thumbnail */}
                  <td 
                    onClick={() => handleRowClick(item)} 
                    style={{ cursor: 'pointer' }}
                  >
                    <img 
                      src={item.image} 
                      className="table-img-cell" 
                      alt="Thumbnail" 
                    />
                  </td>

                  {/* ID */}
                  <td 
                    onClick={() => handleRowClick(item)} 
                    style={{ cursor: 'pointer', fontWeight: 600, color: 'var(--primary-color)' }}
                  >
                    {item.id}
                  </td>

                  {/* Timestamp */}
                  <td 
                    onClick={() => handleRowClick(item)} 
                    style={{ cursor: 'pointer' }}
                  >
                    <div>{item.date}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{item.time}</div>
                  </td>

                  {/* File / Source */}
                  <td 
                    onClick={() => handleRowClick(item)} 
                    style={{ cursor: 'pointer', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                  >
                    {item.imageName}
                  </td>

                  {/* Risk status */}
                  <td 
                    onClick={() => handleRowClick(item)} 
                    style={{ cursor: 'pointer' }}
                  >
                    <span className={`status-badge ${item.status}`}>
                      {item.status === 'healthy' ? 'Healthy' : item.status === 'warning' ? 'Warning' : 'Risk'}
                    </span>
                  </td>

                  {/* Confidence */}
                  <td 
                    onClick={() => handleRowClick(item)} 
                    style={{ cursor: 'pointer', fontWeight: 600 }}
                  >
                    {item.confidence}%
                  </td>

                  {/* Flag indicators */}
                  <td>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      {item.reviewed && (
                        <span 
                          title="Audit completed" 
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '2px',
                            color: 'var(--healthy-color)',
                            backgroundColor: 'var(--healthy-light)',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontSize: '10px',
                            fontWeight: 600
                          }}
                        >
                          <Check size={10} />
                          REV
                        </span>
                      )}
                      {item.flagged && (
                        <span 
                          title="Flagged for Veterinarian" 
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '2px',
                            color: 'var(--warning-color)',
                            backgroundColor: 'var(--warning-light)',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontSize: '10px',
                            fontWeight: 600
                          }}
                        >
                          <Flag size={10} />
                          VET
                        </span>
                      )}
                      {!item.reviewed && !item.flagged && (
                        <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>Pending</span>
                      )}
                    </div>
                  </td>

                  {/* Actions */}
                  <td>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                      
                      {/* Review toggle */}
                      <button
                        onClick={() => onToggleReviewed(item.id)}
                        className={`review-flag-btn ${item.reviewed ? 'reviewed' : ''}`}
                        title={item.reviewed ? "Mark Unreviewed" : "Mark Reviewed"}
                      >
                        <CheckSquare size={16} />
                      </button>

                      {/* Flag toggle */}
                      <button
                        onClick={() => onToggleFlagged(item.id)}
                        className={`review-flag-btn ${item.flagged ? 'flagged' : ''}`}
                        title={item.flagged ? "Unflag Case" : "Flag for Veterinarian"}
                      >
                        <Flag size={16} />
                      </button>

                      {/* Delete item */}
                      <button
                        onClick={() => onRemoveItem(item.id)}
                        className="review-flag-btn"
                        style={{ color: 'var(--text-tertiary)' }}
                        title="Delete record"
                        onMouseEnter={(e) => e.currentTarget.style.color = 'var(--danger-color)'}
                        onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-tertiary)'}
                      >
                        <Trash2 size={16} />
                      </button>

                      {/* View detail page */}
                      <button
                        onClick={() => handleRowClick(item)}
                        className="review-flag-btn"
                        style={{ color: 'var(--primary-color)' }}
                        title="View Report"
                      >
                        <ExternalLink size={16} />
                      </button>
                    </div>
                  </td>

                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Statistics info banner */}
      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', gap: '16px' }}>
        <span>Showing {filteredHistory.length} of {history.length} database logs</span>
        <span>•</span>
        <span>Select any row or click the Report action to inspect visual annotations &amp; veterinary checklists.</span>
      </div>
    </div>
  );
}
