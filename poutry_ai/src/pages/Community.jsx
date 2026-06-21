import React, { useState } from 'react';
import { 
  MessageSquare, 
  HelpCircle, 
  Send, 
  CheckCircle, 
  FileText,
  AlertCircle,
  PlusCircle,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export default function Community({ user }) {
  const [activeTab, setActiveTab] = useState('forum');
  const [faqs, setFaqs] = useState([
    {
      q: 'What are the early visual indicators of Salmonella enteritidis in laying hens?',
      a: ' Salmonella itself doesn\'t always cause distinct visual lesions, but it frequently triggers severe enteritis and diarrhea. This causes sticky, chalky-white or yellowish fecal discharge to build up on the feathers surrounding the vent (known as pasting). Swelling, skin redness (erythema), and cloacal discharge are key screening flags.',
      open: true
    },
    {
      q: 'How does the CloacaScan AI algorithm distinguish between general vent gleet and Salmonella risk?',
      a: 'The model analyzes pixel density, color variance (redness index), and discharge layout. General vent gleet (fungal candidiasis) often presents with cheesy yellow plaques. Salmonella risk scores increase significantly when white, watery discharge is coupled with high tissue inflammation. All warnings should be confirmed via fecal PCR testing.',
      open: false
    },
    {
      q: 'What immediate biosecurity actions should I take when a high-risk alert is triggered?',
      a: 'First, isolate the affected bird immediately. Place her in a warm, clean quarantine pen. Second, sanitize all drinkers and feeders in the source pen. Third, update your boot wash disinfection baths. Finally, flag the case to your attending veterinarian for swab sample collection.',
      open: false
    },
    {
      q: 'How often should I scan my flock for cloacal health?',
      a: 'We recommend scanning a representative sample of 10-20 birds per house weekly. Run immediate targeted scans on any hens showing lethargy, dropped wings, ruffled feathers, or dirty rear plumage.',
      open: false
    }
  ]);

  const [posts, setPosts] = useState([
    {
      id: 1,
      author: 'Sarah Jenkins',
      role: 'Farm Operator',
      date: 'June 15, 2026',
      question: 'Is this chalky build-up normal for 20-week pullets? Screened house 3A and found two birds like this.',
      image: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150" width="100%"><rect width="200" height="150" fill="%23fee2e2"/><circle cx="100" cy="75" r="16" fill="%23f43f5e" fill-opacity="0.6"/><path d="M70,85 C80,95 85,90 95,95" stroke="%23ca8a04" stroke-width="4" stroke-linecap="round"/><path d="M110,85 C120,95 115,90 125,95" stroke="%23f5f5f4" stroke-width="4" stroke-linecap="round"/><text x="100" y="140" text-anchor="middle" font-family="sans-serif" font-size="8" fill="%23ef4444" font-weight="bold">WARNING CASE PREVIEW</text></svg>',
      reply: {
        author: 'Dr. Robert Carter',
        role: 'Chief Poultry Vet',
        date: 'June 15, 2026',
        text: 'This is a clear warning sign. The white chalky pasting points to severe diarrheic discharge, possibly due to Salmonella or severe coccidiosis. Clean the vent with warm sanitizing solution, isolate both birds immediately, and collect a fecal sample for lab PCR. Do not wait.'
      }
    },
    {
      id: 2,
      author: 'David Vance',
      role: 'Assistant Operator',
      date: 'June 14, 2026',
      question: 'Just scanned this hen from house 2B. Cloaca scan returned 96% Healthy score. Feathers look clean, vent pink. Does this look good to go?',
      image: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150" width="100%"><rect width="200" height="150" fill="%23d1fae5"/><circle cx="100" cy="75" r="12" fill="%23fda4af" fill-opacity="0.6" stroke="%23f43f5e"/><text x="100" y="140" text-anchor="middle" font-family="sans-serif" font-size="8" fill="%23059669" font-weight="bold">HEALTHY CASE PREVIEW</text></svg>',
      reply: {
        author: 'Dr. Robert Carter',
        role: 'Chief Poultry Vet',
        date: 'June 14, 2026',
        text: 'Agreed. This represents a normal, healthy cloaca. The skin lining is pink, moisture level is optimal, and surrounding plumage is clean. Keep logging these as baseline references!'
      }
    }
  ]);

  // Form states
  const [newQuestion, setNewQuestion] = useState('');
  const [submittedQuestion, setSubmittedQuestion] = useState(false);
  
  // Ticket states
  const [ticketSubject, setTicketSubject] = useState('');
  const [ticketDescription, setTicketDescription] = useState('');
  const [ticketHouse, setTicketHouse] = useState('House 4B');
  const [ticketSuccess, setTicketSuccess] = useState(false);

  const toggleFaq = (index) => {
    setFaqs(faqs.map((faq, i) => {
      if (i === index) {
        return { ...faq, open: !faq.open };
      }
      return faq;
    }));
  };

  const handlePostSubmit = (e) => {
    e.preventDefault();
    if (!newQuestion.trim()) return;

    const newPost = {
      id: posts.length + 1,
      author: user ? user.name : 'Jane Doe',
      role: user ? (user.role === 'veterinarian' ? 'Attending Vet' : 'Farm Operator') : 'Farm Operator',
      date: 'Just Now',
      question: newQuestion,
      image: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 150" width="100%"><rect width="200" height="150" fill="%23f3f4f6"/><text x="100" y="75" text-anchor="middle" font-family="sans-serif" font-size="8" fill="%239ca3af">USER ATTACHMENT</text></svg>',
      reply: {
        author: 'Dr. Robert Carter',
        role: 'Chief Poultry Vet',
        date: 'Simulated System Response',
        text: 'Thank you for submitting this question. Our veterinary review desk has received it and will respond with advice shortly. In the meantime, please check if the bird shows other symptoms like ruffled feathers or lethargy.'
      }
    };

    setPosts([newPost, ...posts]);
    setNewQuestion('');
    setSubmittedQuestion(true);
    setTimeout(() => setSubmittedQuestion(false), 3000);
  };

  const handleTicketSubmit = (e) => {
    e.preventDefault();
    if (!ticketSubject || !ticketDescription) return;

    setTicketSuccess(true);
    setTicketSubject('');
    setTicketDescription('');
    setTimeout(() => setTicketSuccess(false), 4000);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 700 }}>Agritech Help &amp; Support Centre</h2>
          <p className="page-desc">Consult with poultry veterinarians, review FAQs, and file rapid clinical support tickets</p>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--border-color)',
        marginBottom: '28px',
        gap: '24px'
      }}>
        <button
          onClick={() => setActiveTab('forum')}
          style={{
            border: 'none',
            background: 'none',
            fontSize: '15px',
            fontWeight: 600,
            color: activeTab === 'forum' ? 'var(--primary-color)' : 'var(--text-secondary)',
            borderBottom: activeTab === 'forum' ? '2.5px solid var(--primary-color)' : '2.5px solid transparent',
            paddingBottom: '12px',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)'
          }}
        >
          Community Discussion Board
        </button>

        <button
          onClick={() => setActiveTab('faq')}
          style={{
            border: 'none',
            background: 'none',
            fontSize: '15px',
            fontWeight: 600,
            color: activeTab === 'faq' ? 'var(--primary-color)' : 'var(--text-secondary)',
            borderBottom: activeTab === 'faq' ? '2.5px solid var(--primary-color)' : '2.5px solid transparent',
            paddingBottom: '12px',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)'
          }}
        >
          Frequently Asked Questions
        </button>

        <button
          onClick={() => setActiveTab('ticket')}
          style={{
            border: 'none',
            background: 'none',
            fontSize: '15px',
            fontWeight: 600,
            color: activeTab === 'ticket' ? 'var(--primary-color)' : 'var(--text-secondary)',
            borderBottom: activeTab === 'ticket' ? '2.5px solid var(--primary-color)' : '2.5px solid transparent',
            paddingBottom: '12px',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)'
          }}
        >
          Veterinary Ticket Support
        </button>
      </div>

      {/* Tab contents */}
      <div className="community-layout">
        
        {/* Left main pane */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {activeTab === 'forum' && (
            <div>
              {/* Add post form */}
              <div className="new-post-form">
                <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Ask the Veterinary Community</h3>
                
                {submittedQuestion && (
                  <div style={{
                    display: 'flex',
                    gap: '8px',
                    backgroundColor: 'var(--healthy-light)',
                    color: 'var(--healthy-color)',
                    border: '1px solid var(--healthy-border)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '10px 14px',
                    fontSize: '13px',
                    marginBottom: '16px'
                  }}>
                    <CheckCircle size={16} />
                    <span>Question posted successfully. Simulated Veterinarian reply has been attached.</span>
                  </div>
                )}

                <form onSubmit={handlePostSubmit}>
                  <div className="form-group">
                    <textarea
                      rows="3"
                      className="form-input"
                      placeholder="Describe the clinical symptoms or concerns you have about your chickens (e.g. diarrhea signs, feather condition, house number)..."
                      value={newQuestion}
                      onChange={(e) => setNewQuestion(e.target.value)}
                      style={{ resize: 'vertical' }}
                    />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      Attach photo from current workspace or folder
                    </span>
                    <button type="submit" className="btn btn-primary" style={{ padding: '8px 16px' }}>
                      <Send size={14} />
                      Post Question
                    </button>
                  </div>
                </form>
              </div>

              {/* Forum Feed */}
              <div className="forum-list">
                {posts.map((post) => (
                  <div key={post.id} className="forum-card">
                    <div className="forum-card-header">
                      <div className="forum-card-user">
                        <div className="user-avatar" style={{ width: '32px', height: '32px', fontSize: '12px' }}>
                          {post.author[0]}
                        </div>
                        <div>
                          <div className="forum-card-name">{post.author}</div>
                          <div className="forum-card-meta">{post.role} • {post.date}</div>
                        </div>
                      </div>
                    </div>

                    <div className="forum-card-body">
                      <p>{post.question}</p>
                      {post.image && (
                        <div style={{ width: '130px', marginTop: '10px' }}>
                          <img src={post.image} className="forum-card-img" alt="Post attachment" />
                        </div>
                      )}
                    </div>

                    {post.reply && (
                      <div className="forum-card-replies">
                        <div className="reply-header">
                          <div className="reply-user-info">
                            <span className="reply-user-name">{post.reply.author}</span>
                            <span className="expert-badge">Veterinarian</span>
                          </div>
                          <span className="reply-date">{post.reply.date}</span>
                        </div>
                          <p className="reply-body">{post.reply.text}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'faq' && (
            <div className="faq-list">
              <h3 className="community-section-title">
                <HelpCircle size={18} className="text-primary" style={{ color: 'var(--primary-color)' }} />
                Salmonella Risk Screening FAQ
              </h3>
              
              {faqs.map((faq, idx) => (
                <div key={idx} className="faq-item">
                  <button className="faq-question-btn" onClick={() => toggleFaq(idx)}>
                    <span>{faq.q}</span>
                    {faq.open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                  {faq.open && (
                    <div className="faq-answer">
                      {faq.a}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {activeTab === 'ticket' && (
            <div className="panel">
              <h3 className="community-section-title">
                <FileText size={18} className="text-primary" style={{ color: 'var(--primary-color)' }} />
                Submit Laboratory / Vet Clinic Ticket
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
                Open a high-priority biosecurity ticket to request physical veterinary visits or diagnostic swabs of suspected pens.
              </p>

              {ticketSuccess && (
                <div style={{
                  display: 'flex',
                  gap: '8px',
                  backgroundColor: 'var(--healthy-light)',
                  color: 'var(--healthy-color)',
                  border: '1px solid var(--healthy-border)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '12px 16px',
                  fontSize: '13px',
                  marginBottom: '20px'
                }}>
                  <CheckCircle size={18} style={{ flexShrink: 0 }} />
                  <div>
                    <strong>Ticket Submitted Successfully</strong>
                    <div style={{ fontSize: '12px', marginTop: '2px' }}>
                      Diagnostic Ticket ID: VT-8294. Dr. Robert Carter has been notified.
                    </div>
                  </div>
                </div>
              )}

              <form onSubmit={handleTicketSubmit}>
                <div className="form-group">
                  <label className="form-label">Subject / Incident Title</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. High-risk vent pasting identified in Layer House 4"
                    value={ticketSubject}
                    onChange={(e) => setTicketSubject(e.target.value)}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }} className="form-group">
                  <div>
                    <label className="form-label">Affected Pen / House ID</label>
                    <select
                      className="form-select"
                      value={ticketHouse}
                      onChange={(e) => setTicketHouse(e.target.value)}
                    >
                      <option value="House 4A">Layer House 4A</option>
                      <option value="House 4B">Layer House 4B</option>
                      <option value="House 2A">Pullet House 2A</option>
                      <option value="House 2B">Pullet House 2B</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Priority Level</label>
                    <select className="form-select">
                      <option value="high">High - Suspected Infection</option>
                      <option value="medium">Medium - Checkup needed</option>
                      <option value="low">Low - Routine logging</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Clinical Description &amp; Details</label>
                  <textarea
                    rows="4"
                    className="form-input"
                    placeholder="Specify total birds affected, symptoms noticed (lethargy, feed drop, water intake drop), and if they have been isolated."
                    value={ticketDescription}
                    onChange={(e) => setTicketDescription(e.target.value)}
                    style={{ resize: 'vertical' }}
                  />
                </div>

                <button type="submit" className="btn btn-primary">
                  Submit Veterinary Ticket
                </button>
              </form>
            </div>
          )}

        </div>

        {/* Right side helper info column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          <div className="panel" style={{ borderLeft: '4px solid var(--primary-color)' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '6px' }}>Attending Veterinarian</h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '12px' }}>
              <div className="user-avatar" style={{ width: '44px', height: '44px', fontSize: '15px' }}>
                RC
              </div>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>Dr. Robert Carter</div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Poultry Pathologist</div>
                <div style={{ fontSize: '11px', color: 'var(--primary-color)', fontWeight: 500 }}>Active Now</div>
              </div>
            </div>
          </div>

          <div className="panel" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--danger-color)' }}>
              <AlertCircle size={16} />
              Biosecurity Notice
            </h4>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '8px', lineHeight: '1.5' }}>
              If a chicken tests as a High Risk (Salmonella screening trigger) case:
            </p>
            <ul style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '8px', paddingLeft: '16px', lineHeight: '1.6' }}>
              <li>Isolate chicken immediately.</li>
              <li>Sanitize roosting and nesting logs.</li>
              <li>Wear dedicated gloves when handling.</li>
              <li>Prepare fecal sample swab for Dr. Carter.</li>
            </ul>
          </div>

        </div>

      </div>
    </div>
  );
}
