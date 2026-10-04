'use client';

import { useEffect, useState } from 'react';
import { Topbar } from '@/components/Topbar';
import { Sidebar } from '@/components/Sidebar';
import { contacts, type Contact } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import {
  Users,
  Plus,
  Mail,
  ExternalLink,
  Send,
  Trash2,
  Copy,
  Check,
  X,
  Building2,
  Briefcase,
  Layers,
} from 'lucide-react';

export default function ContactsPage() {
  const { user } = useAuth();
  const [contactList, setContactList] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);

  // New contact form state
  const [showAddModal, setShowAddModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newTitle, setNewTitle] = useState('Recruiter');
  const [newEmail, setNewEmail] = useState('');
  const [newLinkedin, setNewLinkedin] = useState('');
  const [newNotes, setNewNotes] = useState('');

  // Pitch generation state
  const [pitchTarget, setPitchTarget] = useState<Contact | null>(null);
  const [pitchCompany, setPitchCompany] = useState('');
  const [pitchJobTitle, setPitchJobTitle] = useState('Software Engineer');
  const [pitchKeySkill, setPitchKeySkill] = useState('Full Stack & Distributed Systems');
  const [pitchResult, setPitchResult] = useState<{ pitch: string; char_count: number } | null>(null);
  const [pitchLoading, setPitchLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadContacts();
  }, [user]);

  async function loadContacts() {
    setLoading(true);
    try {
      const data = await contacts.list().catch(() => []);
      setContactList(data);
    } catch (err) {
      console.error('Failed to load contacts:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddContact(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;

    try {
      await contacts.create({
        name: newName.trim(),
        title: newTitle.trim() || 'Recruiter',
        email: newEmail.trim() || undefined,
        linkedin_url: newLinkedin.trim() || undefined,
        notes: newNotes.trim() || undefined,
      });
      setShowAddModal(false);
      setNewName('');
      setNewTitle('Recruiter');
      setNewEmail('');
      setNewLinkedin('');
      setNewNotes('');
      await loadContacts();
    } catch (err) {
      console.error('Failed to create contact:', err);
    }
  }

  async function handleDeleteContact(id: string) {
    if (!confirm('Are you sure you want to remove this contact?')) return;
    try {
      await contacts.delete(id);
      setContactList((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      console.error('Failed to delete contact:', err);
    }
  }

  async function handleGeneratePitch(targetContact: Contact) {
    setPitchTarget(targetContact);
    setPitchCompany(targetContact.company_name || 'Target Company');
    setPitchResult(null);
    setPitchLoading(true);
    try {
      const res = await contacts.draftPitch({
        contact_name: targetContact.name,
        contact_title: targetContact.title || 'Recruiter',
        company_name: targetContact.company_name || pitchCompany || 'Hiring Team',
        target_role: pitchJobTitle,
        candidate_skills: [pitchKeySkill],
      });
      setPitchResult({
        pitch: res.pitch_text,
        char_count: res.pitch_text.length,
      });
    } catch (err) {
      console.error('Failed to draft pitch:', err);
    } finally {
      setPitchLoading(false);
    }
  }

  function handleCopyPitch() {
    if (!pitchResult?.pitch) return;
    navigator.clipboard.writeText(pitchResult.pitch);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="app-shell">
      <Topbar />
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <h1 className="page-title">Recruiter Outreach & Networking CRM</h1>
            <p className="page-subtitle">
              Manage recruiter relationships, track outreach channels, and draft &le;300 character LinkedIn connection pitches
            </p>
          </div>

          <button
            className="btn btn-primary"
            onClick={() => setShowAddModal(true)}
          >
            <Plus size={16} />
            <span>Add New Contact</span>
          </button>
        </div>

        {/* Contacts Table / Grid */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {loading ? (
            <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <div
                style={{
                  display: 'inline-block',
                  width: '36px',
                  height: '36px',
                  border: '3px solid var(--border-medium)',
                  borderTopColor: 'var(--accent)',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite',
                  marginBottom: '16px',
                }}
              />
              <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Loading network contacts...</p>
            </div>
          ) : contactList.length === 0 ? (
            <div style={{ padding: '60px 24px', textAlign: 'center' }}>
              <Users size={48} style={{ opacity: 0.3, marginBottom: '16px' }} />
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#fff', marginBottom: '8px' }}>
                No recruiter contacts stored
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.86rem', maxWidth: '420px', margin: '0 auto 20px' }}>
                Add hiring managers, lead recruiters, and referrals to systematically manage touchpoints and automated hook pitches.
              </p>
              <button className="btn btn-primary btn-sm" onClick={() => setShowAddModal(true)}>
                <Plus size={14} />
                <span>Add First Contact</span>
              </button>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', background: 'rgba(255,255,255,0.02)' }}>
                    <th style={{ padding: '16px 20px', fontWeight: 700, color: '#fff' }}>Name & Title</th>
                    <th style={{ padding: '16px 20px', fontWeight: 700, color: '#fff' }}>Channels</th>
                    <th style={{ padding: '16px 20px', fontWeight: 700, color: '#fff' }}>Notes</th>
                    <th style={{ padding: '16px 20px', fontWeight: 700, color: '#fff', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {contactList.map((contact) => {
                    const initials = contact.name.substring(0, 2).toUpperCase();
                    return (
                      <tr
                        key={contact.id}
                        style={{
                          borderBottom: '1px solid var(--border-subtle)',
                          transition: 'background var(--transition-fast)',
                        }}
                      >
                        <td style={{ padding: '16px 20px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div
                              style={{
                                width: '36px',
                                height: '36px',
                                borderRadius: 'var(--r-sm)',
                                background: 'var(--accent-subtle)',
                                border: '1px solid var(--border-subtle)',
                                color: 'var(--accent)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontWeight: 700,
                                fontSize: '0.85rem',
                              }}
                            >
                              {initials}
                            </div>
                            <div>
                              <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{contact.name}</div>
                              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                                {contact.title || 'Recruiter'}
                              </div>
                            </div>
                          </div>
                        </td>

                        <td style={{ padding: '16px 20px' }}>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            {contact.linkedin_url && (
                              <a
                                href={
                                  contact.linkedin_url.startsWith('http')
                                    ? contact.linkedin_url
                                    : `https://${contact.linkedin_url}`
                                }
                                target="_blank"
                                rel="noreferrer"
                                className="badge badge-info"
                                style={{ textDecoration: 'none' }}
                              >
                                <span>LinkedIn</span>
                                <ExternalLink size={10} />
                              </a>
                            )}
                            {contact.email && (
                              <a
                                href={`mailto:${contact.email}`}
                                className="badge badge-neutral"
                                style={{ textDecoration: 'none' }}
                              >
                                <Mail size={11} />
                                <span>Email</span>
                              </a>
                            )}
                          </div>
                        </td>

                        <td style={{ padding: '16px 20px', color: 'var(--text-secondary)', fontSize: '0.82rem', maxWidth: '240px' }}>
                          {contact.notes || '—'}
                        </td>

                        <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => handleGeneratePitch(contact)}
                            >
                              <Send size={13} />
                              <span>Draft Pitch</span>
                            </button>
                            <button
                              className="btn btn-ghost btn-sm"
                              style={{ color: '#fb7185' }}
                              onClick={() => handleDeleteContact(contact.id)}
                              title="Remove contact"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pitch Generation Modal */}
        {pitchTarget && (
          <div className="modal-backdrop" onClick={() => setPitchTarget(null)}>
            <div
              className="modal-dialog"
              onClick={(e) => e.stopPropagation()}
              style={{ maxWidth: '580px' }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '18px',
                  borderBottom: '1px solid var(--border-subtle)',
                  paddingBottom: '12px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Send size={16} style={{ color: 'var(--accent)' }} />
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    LinkedIn Connection Pitch: {pitchTarget.name}
                  </h3>
                </div>
                <button
                  onClick={() => setPitchTarget(null)}
                  className="btn btn-ghost btn-sm"
                  style={{ padding: '6px' }}
                >
                  <X size={18} />
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                <div>
                  <label className="label">Company Name</label>
                  <input
                    type="text"
                    className="input"
                    value={pitchCompany}
                    onChange={(e) => setPitchCompany(e.target.value)}
                    placeholder="e.g. Stripe, OpenAI"
                  />
                </div>
                <div>
                  <label className="label">Target Role</label>
                  <input
                    type="text"
                    className="input"
                    value={pitchJobTitle}
                    onChange={(e) => setPitchJobTitle(e.target.value)}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label className="label">Key Skill / Highlight</label>
                <input
                  type="text"
                  className="input"
                  value={pitchKeySkill}
                  onChange={(e) => setPitchKeySkill(e.target.value)}
                />
              </div>

              <button
                className="btn btn-primary"
                onClick={() => handleGeneratePitch(pitchTarget)}
                disabled={pitchLoading}
                style={{ width: '100%', marginBottom: '18px', padding: '11px' }}
              >
                <Send size={14} />
                <span>{pitchLoading ? 'Generating Hook...' : 'Regenerate Concise Pitch (≤300 Chars)'}</span>
              </button>

              {pitchResult && (
                <div
                  style={{
                    background: 'var(--bg-surface)',
                    borderRadius: 'var(--radius-md)',
                    padding: '18px',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Connection Note Draft
                    </span>
                    <span
                      style={{
                        fontSize: '0.78rem',
                        fontWeight: 700,
                        color: pitchResult.char_count <= 300 ? '#34d399' : '#fb7185',
                      }}
                    >
                      {pitchResult.char_count} / 300 chars
                    </span>
                  </div>

                  <p style={{ fontSize: '0.92rem', lineHeight: '1.6', margin: '0 0 16px 0', whiteSpace: 'pre-wrap', color: '#fff' }}>
                    {pitchResult.pitch}
                  </p>

                  <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={handleCopyPitch}
                    >
                      {copied ? <Check size={14} /> : <Copy size={14} />}
                      <span>{copied ? 'Copied' : 'Copy Pitch'}</span>
                    </button>
                    {pitchTarget.linkedin_url && (
                      <a
                        href={
                          pitchTarget.linkedin_url.startsWith('http')
                            ? pitchTarget.linkedin_url
                            : `https://${pitchTarget.linkedin_url}`
                        }
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-primary btn-sm"
                      >
                        <span>Open LinkedIn</span>
                        <ExternalLink size={12} />
                      </a>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Add Contact Modal */}
        {showAddModal && (
          <div className="modal-backdrop" onClick={() => setShowAddModal(false)}>
            <div
              className="modal-dialog"
              onClick={(e) => e.stopPropagation()}
              style={{ maxWidth: '500px' }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '18px',
                  borderBottom: '1px solid var(--border-subtle)',
                  paddingBottom: '12px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Users size={18} style={{ color: 'var(--accent)' }} />
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    Add Recruiter / Referral Contact
                  </h3>
                </div>
                <button
                  onClick={() => setShowAddModal(false)}
                  className="btn btn-ghost btn-sm"
                  style={{ padding: '6px' }}
                >
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleAddContact}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                  <div>
                    <label className="label">Contact Name *</label>
                    <input
                      type="text"
                      className="input"
                      required
                      placeholder="e.g. Sarah Jenkins"
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="label">Role / Title</label>
                    <input
                      type="text"
                      className="input"
                      placeholder="e.g. Senior Tech Recruiter"
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                  <div>
                    <label className="label">Email Address</label>
                    <input
                      type="email"
                      className="input"
                      placeholder="s.jenkins@company.com"
                      value={newEmail}
                      onChange={(e) => setNewEmail(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="label">LinkedIn Profile URL</label>
                    <input
                      type="text"
                      className="input"
                      placeholder="linkedin.com/in/..."
                      value={newLinkedin}
                      onChange={(e) => setNewLinkedin(e.target.value)}
                    />
                  </div>
                </div>

                <div style={{ marginBottom: '20px' }}>
                  <label className="label">Notes / Follow-up Strategy</label>
                  <textarea
                    className="textarea"
                    rows={2}
                    placeholder="Connected via referral, promised feedback on portfolio by Friday..."
                    value={newNotes}
                    onChange={(e) => setNewNotes(e.target.value)}
                  />
                </div>

                <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setShowAddModal(false)}
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary">
                    Save Contact
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
