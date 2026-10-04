'use client';

import { useEffect, useState } from 'react';
import { Topbar } from '@/components/Topbar';
import { Sidebar } from '@/components/Sidebar';
import { qaBank, type QABankEntry } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import {
  HelpCircle,
  Mail,
  Sparkles,
  Copy,
  Check,
  Send,
  MessageSquare,
  Bookmark,
  Layers,
} from 'lucide-react';

export default function QABankPage() {
  const { user } = useAuth();
  const [entries, setEntries] = useState<QABankEntry[]>([]);
  const [customQuestion, setCustomQuestion] = useState('');
  const [generatedAnswer, setGeneratedAnswer] = useState('');
  const [genLoading, setGenLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const [incomingEmail, setIncomingEmail] = useState('');
  const [replyIntent, setReplyIntent] = useState('schedule_interview');
  const [replyDraft, setReplyDraft] = useState('');
  const [replyLoading, setReplyLoading] = useState(false);

  useEffect(() => {
    async function loadEntries() {
      try {
        const data = await qaBank.list().catch(() => []);
        setEntries(data);
      } catch (err: unknown) {
        console.error(err);
      }
    }
    loadEntries();
  }, [user]);

  async function handleGenerateAnswer() {
    if (!customQuestion.trim()) return;
    setGenLoading(true);
    try {
      const res = await qaBank.generate({
        question: customQuestion,
        save_to_bank: true,
      });
      setGeneratedAnswer(res.answer);
      const updated = await qaBank.list().catch(() => []);
      setEntries(updated);
    } catch (err: unknown) {
      console.error(err);
    } finally {
      setGenLoading(false);
    }
  }

  async function handleDraftReply() {
    if (!incomingEmail.trim()) return;
    setReplyLoading(true);
    try {
      const res = await qaBank.replyDraft({
        incoming_email: incomingEmail,
        intent: replyIntent,
      });
      setReplyDraft(res.email_draft);
    } catch (err: unknown) {
      console.error(err);
    } finally {
      setReplyLoading(false);
    }
  }

  const handleCopyEntry = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="app-shell">
      <Topbar />
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <h1 className="page-title">Master QA Bank & Recruiter Email Copilot</h1>
            <p className="page-subtitle">
              Instant answers for job portal application questions & 1-click professional recruiter email responses
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '24px', marginBottom: '32px' }}>
          {/* Question Answer Generator */}
          <div className="card">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '8px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <HelpCircle size={18} style={{ color: 'var(--accent)' }} />
              <span>Application Portal Auto-Answer</span>
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Paste portal questions (e.g. &ldquo;Why this company?&rdquo;, &ldquo;Proudest technical win&rdquo;) to generate resume-aligned answers.
            </p>

            <textarea
              className="textarea"
              rows={3}
              style={{ marginBottom: '14px' }}
              placeholder="e.g., Describe a time you resolved a critical production outage or architecture bottleneck..."
              value={customQuestion}
              onChange={(e) => setCustomQuestion(e.target.value)}
            />

            <button
              onClick={handleGenerateAnswer}
              disabled={genLoading || !customQuestion.trim()}
              className="btn btn-primary btn-sm"
              style={{ width: '100%', padding: '11px', marginBottom: '16px' }}
            >
              <Send size={14} />
              <span>{genLoading ? 'Synthesizing Answer...' : 'Generate & Save to Bank'}</span>
            </button>

            {generatedAnswer && (
              <div
                style={{
                  background: 'var(--bg-surface)',
                  padding: '16px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-accent)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase' }}>
                    Generated Answer
                  </span>
                  <button
                    onClick={() => handleCopyEntry('gen', generatedAnswer)}
                    className="btn btn-secondary btn-sm"
                    style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                  >
                    {copiedId === 'gen' ? <Check size={12} /> : <Copy size={12} />}
                    <span>{copiedId === 'gen' ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                  {generatedAnswer}
                </p>
              </div>
            )}
          </div>

          {/* Email Reply Assistant */}
          <div className="card">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '8px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Mail size={18} style={{ color: '#38bdf8' }} />
              <span>Recruiter Email Reply Drafter</span>
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Paste any recruiter email to compose an intelligent, context-aware reply in seconds.
            </p>

            <textarea
              className="textarea"
              rows={3}
              style={{ marginBottom: '14px' }}
              placeholder="Paste the recruiter's incoming message or invitation here..."
              value={incomingEmail}
              onChange={(e) => setIncomingEmail(e.target.value)}
            />

            <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
              <select
                className="select"
                style={{ flex: 1 }}
                value={replyIntent}
                onChange={(e) => setReplyIntent(e.target.value)}
              >
                <option value="schedule_interview">Schedule Interview Availability</option>
                <option value="negotiate">Negotiate / Counter-Offer</option>
                <option value="follow_up">Gentle Follow-Up on Status</option>
                <option value="decline">Politely Decline Opportunity</option>
              </select>

              <button
                onClick={handleDraftReply}
                disabled={replyLoading || !incomingEmail.trim()}
                className="btn btn-primary btn-sm"
                style={{ whiteSpace: 'nowrap' }}
              >
                <Send size={14} />
                <span>{replyLoading ? 'Drafting...' : 'Draft Reply'}</span>
              </button>
            </div>

            {replyDraft && (
              <div
                style={{
                  background: 'var(--bg-surface)',
                  padding: '16px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-medium)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase' }}>
                    Drafted Response
                  </span>
                  <button
                    onClick={() => handleCopyEntry('reply', replyDraft)}
                    className="btn btn-secondary btn-sm"
                    style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                  >
                    {copiedId === 'reply' ? <Check size={12} /> : <Copy size={12} />}
                    <span>{copiedId === 'reply' ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
                <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.6, whiteSpace: 'pre-wrap', margin: 0 }}>
                  {replyDraft}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Master QA Bank List */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">
                <Bookmark size={18} style={{ color: '#fbbf24' }} />
                <span>Saved Master QA Bank ({entries.length})</span>
              </h3>
              <p className="card-subtitle">Pre-verified answers stored for quick copy-paste into ATS forms</p>
            </div>
          </div>

          {entries.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 16px', color: 'var(--text-muted)' }}>
              <HelpCircle size={36} style={{ opacity: 0.3, marginBottom: '8px' }} />
              <p style={{ fontSize: '0.88rem' }}>No saved answers in your QA Bank yet.</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '14px', marginTop: '12px' }}>
              {entries.map((entry) => (
                <div
                  key={entry.id}
                  style={{
                    padding: '16px 18px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                      {entry.question_key}
                    </span>
                    <button
                      onClick={() => handleCopyEntry(entry.id, entry.answer)}
                      className="btn btn-secondary btn-sm"
                      style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                    >
                      {copiedId === entry.id ? <Check size={12} /> : <Copy size={12} />}
                      <span>{copiedId === entry.id ? 'Copied' : 'Copy Answer'}</span>
                    </button>
                  </div>
                  <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.55, margin: 0 }}>
                    {entry.answer}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
