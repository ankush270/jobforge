'use client';

import { useEffect, useState } from 'react';
import { Topbar } from '@/components/Topbar';
import { Sidebar } from '@/components/Sidebar';
import { coverLetters, jobs, resumes, type CoverLetter, type Job, type Resume } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import {
  Mail,
  FileText,
  Copy,
  Check,
  AlertTriangle,
  Send,
  Briefcase,
  Layers,
} from 'lucide-react';

export default function CoverLetterPage() {
  const { user } = useAuth();
  const [jobList, setJobList] = useState<Job[]>([]);
  const [myResumes, setMyResumes] = useState<Resume[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [selectedResumeId, setSelectedResumeId] = useState<string>('');
  const [mode, setMode] = useState<'cover_letter' | 'email'>('cover_letter');
  const [loading, setLoading] = useState(false);
  const [letterContent, setLetterContent] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const [savedLetters, setSavedLetters] = useState<CoverLetter[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [j, r, cl] = await Promise.all([
          jobs.list({ page: 1 }).catch(() => ({ jobs: [] })),
          resumes.list().catch(() => []),
          coverLetters.list().catch(() => []),
        ]);
        const jobsArr = (j as { jobs: Job[] }).jobs || [];
        setJobList(jobsArr);
        if (jobsArr.length > 0) setSelectedJobId(jobsArr[0].id);

        setMyResumes(r as Resume[]);
        if (r.length > 0) setSelectedResumeId(r[0].id);

        setSavedLetters(cl as CoverLetter[]);
      } catch (err: unknown) {
        console.error(err);
      }
    }
    loadData();
  }, [user]);

  async function handleGenerate() {
    if (!selectedJobId) {
      setError('Please select a target job from the dropdown.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await coverLetters.generate({
        job_id: selectedJobId,
        resume_id: selectedResumeId || undefined,
        mode,
      });
      setLetterContent(result.content);
      setSavedLetters((prev) => [result, ...prev]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Generation failed.');
    } finally {
      setLoading(false);
    }
  }

  function handleCopy() {
    navigator.clipboard.writeText(letterContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  }

  return (
    <div className="app-shell">
      <Topbar />
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <h1 className="page-title">AI Cover Letter & Cold Outreach Pitch</h1>
            <p className="page-subtitle">
              Synthesize 3-paragraph research-backed letters or high-conversion 75-word recruiter cold emails
            </p>
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

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '24px' }}>
          {/* Form Card */}
          <div className="card">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} style={{ color: 'var(--accent)' }} />
              <span>Target Role & Format</span>
            </h3>

            <div style={{ marginBottom: '16px' }}>
              <label className="label">Target Job Role</label>
              <select
                className="select"
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(e.target.value)}
              >
                {jobList.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title} — {j.company?.name || 'Company'}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label className="label">Format Mode</label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setMode('cover_letter')}
                  className={`btn btn-sm ${mode === 'cover_letter' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ flex: 1, padding: '10px' }}
                >
                  <FileText size={15} />
                  <span>3-Para Cover Letter</span>
                </button>
                <button
                  type="button"
                  onClick={() => setMode('email')}
                  className={`btn btn-sm ${mode === 'email' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ flex: 1, padding: '10px' }}
                >
                  <Mail size={15} />
                  <span>75-Word Cold Email</span>
                </button>
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={loading || !selectedJobId}
              className="btn btn-primary"
              style={{ width: '100%', padding: '12px' }}
            >
              <Send size={15} />
              <span>{loading ? 'Crafting Targeted Letter...' : 'Generate Targeted Letter'}</span>
            </button>
          </div>

          {/* Editor & Preview Card */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '14px',
              }}
            >
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
                Generated Output
              </h3>
              {letterContent && (
                <button onClick={handleCopy} className="btn btn-secondary btn-sm">
                  {copied ? <Check size={14} /> : <Copy size={14} />}
                  <span>{copied ? 'Copied!' : 'Copy to Clipboard'}</span>
                </button>
              )}
            </div>

            <textarea
              className="textarea"
              rows={14}
              value={letterContent}
              onChange={(e) => setLetterContent(e.target.value)}
              placeholder="Select a target role and click 'Generate AI Pitch' to craft a tailored letter with quantified STAR achievements..."
              style={{ lineHeight: 1.6, fontSize: '0.9rem' }}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
