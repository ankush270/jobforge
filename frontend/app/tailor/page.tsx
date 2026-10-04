'use client';

import { useEffect, useState } from 'react';
import { Topbar } from '@/components/Topbar';
import { Sidebar } from '@/components/Sidebar';
import {
  evaluations,
  getToken,
  jobs,
  resumes,
  type Job,
  type Resume,
  type TailoredResume,
  type UpskillResult,
} from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import {
  Sparkles,
  FileText,
  Briefcase,
  Download,
  Code,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  BookOpen,
  ArrowRight,
  TrendingUp,
  Clock,
  Layers,
} from 'lucide-react';

export default function TailorPage() {
  const { user } = useAuth();
  const [myResumes, setMyResumes] = useState<Resume[]>([]);
  const [jobList, setJobList] = useState<Job[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>('');
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [tailoredResult, setTailoredResult] = useState<TailoredResume | null>(null);
  const [upskillResult, setUpskillResult] = useState<UpskillResult | null>(null);
  const [upskillLoading, setUpskillLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [r, j] = await Promise.all([
          resumes.list().catch(() => []),
          jobs.list({ page: 1 }).catch(() => ({ jobs: [] })),
        ]);
        setMyResumes(r as Resume[]);
        if (r.length > 0) setSelectedResumeId(r[0].id);

        const jList = (j as { jobs: Job[] }).jobs || [];
        setJobList(jList);
        if (jList.length > 0) setSelectedJobId(jList[0].id);
      } catch (err: unknown) {
        console.error(err);
      }
    }
    loadData();
  }, [user]);

  async function handleTailor() {
    if (!selectedResumeId || !selectedJobId) {
      setError('Please select both a master resume and a target job opening.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await evaluations.tailor({
        resume_id: selectedResumeId,
        job_id: selectedJobId,
      });
      setTailoredResult(res);
      handleUpskill(selectedResumeId, selectedJobId);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Tailoring failed.');
    } finally {
      setLoading(false);
    }
  }

  async function handleUpskill(rId?: string, jId?: string) {
    const resumeId = rId || selectedResumeId;
    const jobId = jId || selectedJobId;
    if (!resumeId || !jobId) return;

    setUpskillLoading(true);
    try {
      const data = await evaluations.upskillGap(resumeId, jobId);
      setUpskillResult(data);
    } catch (e) {
      console.error('Upskill gap fetch error:', e);
    } finally {
      setUpskillLoading(false);
    }
  }

  async function handleDownloadPdf() {
    if (!tailoredResult) return;
    const token = getToken();
    const url = evaluations.tailoredPdfUrl(tailoredResult.id);
    try {
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error('PDF generation failed');
      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `Tailored_Resume_${selectedJob?.title || 'ATS'}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert('Could not download PDF: ' + err);
    }
  }

  async function handleDownloadLatex() {
    if (!tailoredResult) return;
    const token = getToken();
    const url = evaluations.tailoredLatexPdfUrl(tailoredResult.id);
    try {
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error('LaTeX generation failed');
      const contentType = res.headers.get('content-type') || '';
      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      const ext = contentType.includes('pdf') ? 'pdf' : 'tex';
      a.download = `Tailored_Resume_${selectedJob?.title || 'ATS'}_latex.${ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert('Could not download LaTeX: ' + err);
    }
  }

  const selectedJob = jobList.find((j) => j.id === selectedJobId);

  return (
    <div className="app-shell">
      <Topbar />
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <h1 className="page-title">AI Resume Tailor & ATS Optimizer</h1>
            <p className="page-subtitle">
              Transform standard bullets into STAR accomplishment statements with anti-hallucination guard
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

        {/* Setup Workspace Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px', marginBottom: '28px' }}>
          {/* Controls Card */}
          <div className="card">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} style={{ color: 'var(--accent)' }} />
              <span>Step 1: Choose Source & Target</span>
            </h3>

            <div style={{ marginBottom: '16px' }}>
              <label className="label">Master Resume</label>
              <select
                className="select"
                value={selectedResumeId}
                onChange={(e) => setSelectedResumeId(e.target.value)}
              >
                {myResumes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.filename || 'Uploaded Resume'} {r.is_master ? '(Master Profile)' : ''}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: '22px' }}>
              <label className="label">Target Job Opening</label>
              <select
                className="select"
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(e.target.value)}
              >
                {jobList.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title} — {j.company?.name || 'Company'} ({j.location || 'Remote'})
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={handleTailor}
                disabled={loading || !selectedResumeId || !selectedJobId}
                className="btn btn-primary"
                style={{ flex: 1, padding: '12px' }}
              >
                <Sparkles size={16} />
                <span>{loading ? 'Running STAR Engine...' : 'Generate Tailored Resume'}</span>
              </button>

              <button
                onClick={() => handleUpskill()}
                disabled={upskillLoading || !selectedResumeId || !selectedJobId}
                className="btn btn-secondary"
                style={{ padding: '12px 18px' }}
                title="Analyze skill gaps & proof-of-work project roadmap"
              >
                <BookOpen size={16} />
                <span>{upskillLoading ? 'Analyzing...' : 'Upskill Gaps'}</span>
              </button>
            </div>
          </div>

          {/* Job Preview Card */}
          <div className="card">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '12px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Briefcase size={18} style={{ color: '#38bdf8' }} />
              <span>Target Role Context</span>
            </h3>

            {selectedJob ? (
              <div style={{ fontSize: '0.86rem', color: 'var(--text-secondary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontWeight: 700, color: '#fff', fontSize: '1rem' }}>
                    {selectedJob.title}
                  </span>
                  <span className="badge badge-info">{selectedJob.company?.name}</span>
                </div>
                <div
                  style={{
                    maxHeight: '180px',
                    overflowY: 'auto',
                    background: 'var(--bg-surface)',
                    padding: '12px',
                    borderRadius: 'var(--radius-sm)',
                    lineHeight: 1.6,
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <p style={{ whiteSpace: 'pre-wrap' }}>
                    {selectedJob.description.slice(0, 600)}...
                  </p>
                </div>
              </div>
            ) : (
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Select a job from your feed to view requirement specs.
              </p>
            )}
          </div>
        </div>

        {/* Results Panel */}
        {tailoredResult && (
          <div className="card" style={{ marginBottom: '32px' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '20px',
                borderBottom: '1px solid var(--border-subtle)',
                paddingBottom: '18px',
                flexWrap: 'wrap',
                gap: '16px',
              }}
            >
              <div>
                <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle2 size={20} style={{ color: '#10b981' }} />
                  <span>Tailored Resume Ready</span>
                </h2>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginTop: '6px' }}>
                  <span
                    className="badge badge-success"
                    style={{ fontSize: '0.75rem' }}
                  >
                    <ShieldCheck size={12} />
                    <span>Fact Guard: {tailoredResult.fact_check_status.toUpperCase()}</span>
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#34d399', lineHeight: 1 }}>
                    {tailoredResult.ats_score}%
                  </div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    ATS Match Score
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button onClick={handleDownloadPdf} className="btn btn-primary btn-sm">
                    <Download size={14} />
                    <span>ATS PDF</span>
                  </button>
                  <button onClick={handleDownloadLatex} className="btn btn-secondary btn-sm">
                    <Code size={14} />
                    <span>LaTeX</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Keyword gaps */}
            {tailoredResult.missing_keywords && tailoredResult.missing_keywords.length > 0 && (
              <div style={{ marginBottom: '24px' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px' }}>
                  Target Keywords Integrated into STAR Bullets:
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {tailoredResult.missing_keywords.map((kw, i) => (
                    <span key={i} className="badge badge-warning" style={{ fontSize: '0.75rem' }}>
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Rewritten Work Experience Preview */}
            <div>
              <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginBottom: '14px' }}>
                STAR Rewritten Bullets (Anti-Hallucination Verified):
              </h4>
              {((tailoredResult.content?.workExperience as Array<{ company?: string; title?: string; bullets?: string[] }>) || []).map((exp, idx) => (
                <div
                  key={idx}
                  style={{
                    marginBottom: '16px',
                    background: 'var(--bg-surface)',
                    padding: '18px 20px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.98rem', marginBottom: '10px' }}>
                    {exp.title} &middot; <span style={{ color: 'var(--accent)' }}>{exp.company}</span>
                  </div>
                  <ul style={{ paddingLeft: '20px', margin: 0 }}>
                    {(exp.bullets || []).map((b, bi) => (
                      <li key={bi} style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '8px', lineHeight: 1.55 }}>
                        {b}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Upskill Gap Analysis */}
        {upskillResult && (
          <div className="card">
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '18px',
                borderBottom: '1px solid var(--border-subtle)',
                paddingBottom: '14px',
              }}
            >
              <div>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BookOpen size={20} style={{ color: 'var(--accent)' }} />
                  <span>Upskill Gap Analysis & Portfolio Roadmap</span>
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Targeted projects to boost your match from{' '}
                  <strong style={{ color: '#fbbf24' }}>{upskillResult.current_fit_score}%</strong> to{' '}
                  <strong style={{ color: '#34d399' }}>{upskillResult.projected_fit_score}%</strong>
                </p>
              </div>
            </div>

            {/* Critical Skill Gaps */}
            <div style={{ marginBottom: '24px' }}>
              <h4 style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '10px' }}>
                Key Competencies to Bridge:
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '12px' }}>
                {upskillResult.critical_skill_gaps.map((gap, i) => (
                  <div
                    key={i}
                    style={{
                      background: 'rgba(244, 63, 94, 0.08)',
                      border: '1px solid rgba(244, 63, 94, 0.25)',
                      padding: '14px',
                      borderRadius: 'var(--radius-md)',
                    }}
                  >
                    <div style={{ fontWeight: 700, color: '#fb7185', fontSize: '0.92rem' }}>{gap.skill}</div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: 1.4 }}>
                      {gap.reason}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Proof-of-work projects */}
            <div>
              <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#fff', marginBottom: '12px' }}>
                Recommended Proof-of-Work Portfolio Projects:
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '16px' }}>
                {upskillResult.proof_of_work_projects.map((proj, pi) => (
                  <div
                    key={pi}
                    style={{
                      background: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '18px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.98rem' }}>{proj.title}</span>
                      <span className="badge badge-info" style={{ fontSize: '0.72rem' }}>
                        {proj.time_estimate}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '12px', lineHeight: 1.5 }}>
                      {proj.description}
                    </p>
                    <div
                      style={{
                        background: 'var(--accent-subtle)',
                        border: '1px solid var(--border-accent)',
                        padding: '10px 12px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.8rem',
                        color: 'var(--text-secondary)',
                        fontStyle: 'italic',
                      }}
                    >
                      &ldquo;{proj.resume_bullet_preview}&rdquo;
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
