'use client';

import { useEffect, useState } from 'react';
import { Topbar } from '@/components/Topbar';
import { Sidebar } from '@/components/Sidebar';
import { interviews, jobs, type Interview, type Job } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import {
  Mic,
  Sparkles,
  HelpCircle,
  Star,
  MessageSquare,
  ShieldAlert,
  Calendar,
  AlertTriangle,
  Briefcase,
  ChevronRight,
  Layers,
} from 'lucide-react';

export default function InterviewPrepPage() {
  const { user } = useAuth();
  const [jobList, setJobList] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [activePrep, setActivePrep] = useState<Interview | null>(null);
  const [pastPreps, setPastPreps] = useState<Interview[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [j, ip] = await Promise.all([
          jobs.list({ page: 1 }).catch(() => ({ jobs: [] })),
          interviews.list().catch(() => []),
        ]);
        const jArr = (j as { jobs: Job[] }).jobs || [];
        setJobList(jArr);
        if (jArr.length > 0) setSelectedJobId(jArr[0].id);

        setPastPreps(ip as Interview[]);
        if (ip.length > 0) setActivePrep(ip[0]);
      } catch (err: unknown) {
        console.error(err);
      }
    }
    loadData();
  }, [user]);

  async function handleGenerate() {
    if (!selectedJobId) {
      setError('Please select a target job opening.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await interviews.prep({ job_id: selectedJobId });
      setActivePrep(res);
      setPastPreps((prev) => [res, ...prev]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Interview prep generation failed.');
    } finally {
      setLoading(false);
    }
  }

  const notes = activePrep?.prep_notes;

  return (
    <div className="app-shell">
      <Topbar />
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <h1 className="page-title">AI Interview Prep & STAR Story Bank</h1>
            <p className="page-subtitle">
              Predict behavioral and system design questions, rehearse verified STAR stories, and spot culture red flags
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <select
              className="select"
              style={{ minWidth: '260px' }}
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
            >
              {jobList.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} — {j.company?.name || 'Company'}
                </option>
              ))}
            </select>
            <button
              onClick={handleGenerate}
              disabled={loading || !selectedJobId}
              className="btn btn-primary"
            >
              <Sparkles size={16} />
              <span>{loading ? 'Synthesizing Pack...' : 'Generate Prep Pack'}</span>
            </button>
          </div>
        </div>

        {error && (
          <div
            style={{
              padding: '14px 18px',
              background: 'rgba(244, 63, 94, 0.12)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              borderRadius: 'var(--radius-md)',
              color: '#fb7185',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}

        {notes ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '24px' }}>
            {/* Left Column: Questions & STAR Stories */}
            <div>
              {/* Predicted Questions */}
              <div className="card" style={{ marginBottom: '24px' }}>
                <div className="card-header">
                  <div>
                    <h3 className="card-title">
                      <HelpCircle size={18} style={{ color: 'var(--accent)' }} />
                      <span>Predicted Technical & Behavioral Questions</span>
                    </h3>
                    <p className="card-subtitle">Derived from job requirements and role seniority</p>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '12px' }}>
                  {(notes.predicted_questions || []).map((q, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '16px 18px',
                        borderRadius: 'var(--radius-md)',
                        background: 'var(--bg-surface)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span className="badge badge-info" style={{ textTransform: 'uppercase', fontSize: '0.68rem' }}>
                          {q.category}
                        </span>
                      </div>
                      <p style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px', fontSize: '0.98rem' }}>
                        {q.question}
                      </p>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '10px', fontStyle: 'italic' }}>
                        Evaluates: {q.why_they_ask}
                      </p>
                      <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        <strong style={{ color: '#fff' }}>Recommended Talking Points:</strong>
                        <ul style={{ margin: '4px 0 0 0', paddingLeft: '18px' }}>
                          {(q.key_talking_points || []).map((pt, pti) => (
                            <li key={pti} style={{ marginBottom: '4px', lineHeight: 1.45 }}>
                              {pt}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* STAR Stories */}
              <div className="card">
                <div className="card-header">
                  <div>
                    <h3 className="card-title">
                      <Star size={18} style={{ color: '#fbbf24' }} />
                      <span>STAR Story Bank (Tailored to Candidate Experience)</span>
                    </h3>
                    <p className="card-subtitle">Structured answers for high-pressure rounds</p>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '12px' }}>
                  {(notes.star_stories || []).map((s, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '18px',
                        borderRadius: 'var(--radius-md)',
                        background: 'var(--bg-surface)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div
                        style={{
                          fontWeight: 800,
                          color: 'var(--accent)',
                          marginBottom: '10px',
                          fontSize: '0.98rem',
                        }}
                      >
                        {s.theme}
                      </div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'grid', gap: '8px' }}>
                        <div>
                          <strong style={{ color: 'var(--text-primary)' }}>Situation:</strong> {s.situation}
                        </div>
                        <div>
                          <strong style={{ color: 'var(--text-primary)' }}>Task:</strong> {s.task}
                        </div>
                        <div>
                          <strong style={{ color: 'var(--text-primary)' }}>Action:</strong> {s.action}
                        </div>
                        <div style={{ background: 'var(--accent-subtle)', padding: '8px 12px', borderRadius: 'var(--radius-sm)' }}>
                          <strong style={{ color: 'var(--accent)' }}>Quantified Result:</strong> {s.result}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: Reverse Questions, Red Flags & Study Plan */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Reverse Questions */}
              <div className="card">
                <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <MessageSquare size={17} style={{ color: 'var(--accent)' }} />
                  <span>Strategic Questions to Ask Interviewers</span>
                </h4>
                <ul style={{ paddingLeft: '18px', margin: 0, fontSize: '0.86rem', color: 'var(--text-secondary)' }}>
                  {(notes.reverse_questions_to_ask || []).map((rq, idx) => (
                    <li key={idx} style={{ marginBottom: '10px', lineHeight: 1.5 }}>
                      {rq}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Culture Red Flags */}
              <div
                className="card"
                style={{
                  borderLeft: '4px solid #f43f5e',
                }}
              >
                <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#fb7185', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldAlert size={18} />
                  <span>Culture & Operational Red Flags to Watch</span>
                </h4>
                <ul style={{ paddingLeft: '18px', margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {(notes.culture_red_flags_to_watch || []).map((rf, idx) => (
                    <li key={idx} style={{ marginBottom: '8px', lineHeight: 1.45 }}>
                      {rf}
                    </li>
                  ))}
                </ul>
              </div>

              {/* 3-Day Study Plan */}
              <div className="card">
                <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Calendar size={17} style={{ color: 'var(--accent)' }} />
                  <span>3-Day Sprint Preparation Plan</span>
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {(notes.study_plan || []).map((day, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '10px 14px',
                        background: 'var(--bg-surface)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                      }}
                    >
                      <span className="badge badge-info" style={{ fontSize: '0.72rem', flexShrink: 0 }}>
                        Day {day.day}
                      </span>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        {day.focus}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="card" style={{ padding: '60px 40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <Mic size={48} style={{ opacity: 0.3, marginBottom: '16px' }} />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff', marginBottom: '8px' }}>
              No interview prep pack generated yet
            </h2>
            <p style={{ maxWidth: '440px', margin: '0 auto 20px', fontSize: '0.88rem' }}>
              Select a target role from your jobs feed above and click &ldquo;Generate Prep Pack&rdquo; to build your personalized question forecast and STAR story vault.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
