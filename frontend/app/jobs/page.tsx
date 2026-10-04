'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  applications,
  companies,
  evaluations,
  hasToken,
  jobs,
  type CompanyIntelResult,
  type Job,
  type JobEvaluationResult,
} from '@/lib/api';
import { Topbar } from '@/components/Topbar';
import { Sidebar } from '@/components/Sidebar';
import { useAuth } from '@/lib/auth-context';
import { ScrapeJobsModal } from '@/components/ScrapeJobsModal';
import {
  Search,
  MapPin,
  Building2,
  DollarSign,
  Calendar,
  Ghost,
  Target,
  BookmarkPlus,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Filter,
  X,
  Plus,
  Star,
  ShieldAlert,
} from 'lucide-react';

export default function JobsPage() {
  const { user } = useAuth();
  const [jobList, setJobList] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [platform, setPlatform] = useState('');
  const [loading, setLoading] = useState(true);
  const [scrapeOpen, setScrapeOpen] = useState(false);

  // Company Intel State
  const [selectedCompanyIntel, setSelectedCompanyIntel] = useState<CompanyIntelResult | null>(null);
  const [intelLoading, setIntelLoading] = useState(false);

  // 8-Block Evaluation State
  const [selectedEval, setSelectedEval] = useState<JobEvaluationResult | null>(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalJob, setEvalJob] = useState<Job | null>(null);

  const [notification, setNotification] = useState<string | null>(null);

  const loadJobs = async () => {
    if (!hasToken()) {
      setJobList([]);
      setTotal(0);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const res = await jobs.list({
        page,
        search: search || undefined,
        platform: platform || undefined,
      });
      setJobList(res.jobs);
      setTotal(res.total);
    } catch {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, [page, user]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadJobs();
  };

  const handleOpenCompanyIntel = async (companyName: string) => {
    setIntelLoading(true);
    try {
      const intel = await companies.intel(companyName);
      setSelectedCompanyIntel(intel);
    } catch (err) {
      console.error('Company intel error:', err);
      alert('Could not fetch company intel.');
    } finally {
      setIntelLoading(false);
    }
  };

  const handleEvaluate = async (job: Job) => {
    setEvalJob(job);
    setEvalLoading(true);
    try {
      const res = await evaluations.jobEval(job.id);
      setSelectedEval(res);
    } catch (err) {
      console.error('Evaluation error:', err);
      alert('Evaluation failed.');
    } finally {
      setEvalLoading(false);
    }
  };

  const handleSaveToPipeline = async (jobId: string) => {
    try {
      await applications.create({ job_id: jobId, status: 'saved' });
      setNotification('Job saved to Kanban tracker.');
      setTimeout(() => setNotification(null), 3000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Could not save job.');
    }
  };

  return (
    <div className="app-shell">
      <Topbar />
      <Sidebar />

      <main className="main-content">
        {/* Ambient Dark Luxury Orb */}
        <div className="hero-orb" />

        {/* Page Header */}
        <div className="page-header">
          <div>
            <div className="page-badge">
              <Target size={13} style={{ color: 'var(--accent)' }} />
              <span>MARKETPLACE INTELLIGENCE</span>
            </div>
            <h1 className="page-title" style={{ marginTop: '6px' }}>
              Parsed Opportunities & Live Feeds
            </h1>
            <p className="page-subtitle">
              {total} verified positions indexed across LinkedIn, Indeed, Ashby, Greenhouse & Lever.
            </p>
          </div>
          <button
            id="scrape-jobs-btn"
            className="btn btn-primary"
            onClick={() => setScrapeOpen(true)}
          >
            <Plus size={14} />
            <span>Scrape Jobs</span>
          </button>
          <ScrapeJobsModal
            open={scrapeOpen}
            onClose={() => setScrapeOpen(false)}
            onDone={() => {
              setPage(1);
              loadJobs();
            }}
          />
        </div>

        {/* Notification */}
        {notification && (
          <div
            style={{
              padding: '8px 14px',
              background: '#16161a',
              border: '1px solid #27272a',
              borderRadius: 'var(--radius-sm)',
              color: '#34d399',
              marginBottom: '16px',
              fontSize: '0.82rem',
            }}
          >
            ✓ {notification}
          </div>
        )}

        {/* Search & Filter Bar */}
        <div style={{ marginBottom: '16px' }}>
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '240px', position: 'relative' }}>
              <Search
                size={14}
                style={{
                  position: 'absolute',
                  left: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)',
                }}
              />
              <input
                className="input"
                placeholder="Filter by title, company, or skill..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ paddingLeft: '32px' }}
              />
            </div>

            <select
              className="select"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              style={{ width: '160px' }}
            >
              <option value="">All Platforms</option>
              <option value="linkedin">LinkedIn</option>
              <option value="indeed">Indeed</option>
              <option value="naukri">Naukri</option>
              <option value="glassdoor">Glassdoor</option>
              <option value="greenhouse">Greenhouse</option>
              <option value="lever">Lever</option>
              <option value="ashby">Ashby</option>
              <option value="manual">Manual</option>
            </select>

            <button type="submit" className="btn btn-secondary">
              <Filter size={13} />
              <span>Search</span>
            </button>
          </form>
        </div>

        {/* Jobs List */}
        <div className="job-list">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px 16px', color: 'var(--text-muted)' }}>
              <p style={{ fontSize: '0.85rem' }}>Loading jobs...</p>
            </div>
          ) : jobList.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '48px 16px', color: 'var(--text-muted)' }}>
              <Building2 size={36} style={{ opacity: 0.3, marginBottom: '12px' }} />
              <p style={{ fontWeight: 500, color: '#fff', marginBottom: '4px' }}>No jobs match your filter</p>
              <p style={{ fontSize: '0.82rem', marginBottom: '16px' }}>
                Adjust your query or scrape new listings from job portals.
              </p>
              <button className="btn btn-secondary btn-sm" onClick={() => setScrapeOpen(true)}>
                Scrape jobs
              </button>
            </div>
          ) : (
            jobList.map((job) => {
              const companyInitials = (job.company?.name || 'JB').substring(0, 2).toUpperCase();
              const hasSalary = job.salary_min && job.salary_max;
              const skillsList = Array.isArray(job.keywords?.required_skills)
                ? (job.keywords.required_skills as string[])
                : [];

              return (
                <div key={job.id} className="job-card">
                  <div className="job-card-main">
                    <div className="job-card-avatar">{companyInitials}</div>

                    <div className="job-card-content">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                        <button
                          onClick={() => handleOpenCompanyIntel(job.company?.name || 'Company')}
                          style={{
                            background: 'none',
                            border: 'none',
                            padding: 0,
                            cursor: 'pointer',
                            textAlign: 'left',
                          }}
                        >
                          <span className="job-card-company">
                            {job.company?.name || 'Undisclosed'}
                          </span>
                        </button>

                        {job.company?.tier && (
                          <span className="badge badge-neutral" style={{ fontSize: '0.68rem' }}>
                            {job.company.tier}
                          </span>
                        )}

                        {job.is_ghost && (
                          <span className="ghost-badge">
                            <Ghost size={11} /> Ghost Job
                          </span>
                        )}
                      </div>

                      <div className="job-card-title">{job.title}</div>

                      <div className="job-card-meta">
                        {job.location && (
                          <span className="job-meta-item">
                            <MapPin size={11} /> {job.location}
                          </span>
                        )}

                        {hasSalary && (
                          <span className="salary-tag">
                            <DollarSign size={11} />
                            {job.salary_currency} {(job.salary_min! / 100000).toFixed(1)}L – {(job.salary_max! / 100000).toFixed(1)}L
                          </span>
                        )}

                        <span className="badge badge-neutral" style={{ textTransform: 'capitalize' }}>
                          {job.source_platform}
                        </span>

                        {job.remote_type && (
                          <span className="job-meta-item">
                            {job.remote_type}
                          </span>
                        )}

                        {job.posted_at && (
                          <span className="job-meta-item">
                            <Calendar size={11} /> {new Date(job.posted_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>

                      {skillsList.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '8px' }}>
                          {skillsList.slice(0, 6).map((skill) => (
                            <span
                              key={skill}
                              className="badge badge-neutral"
                              style={{ fontSize: '0.7rem' }}
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="job-card-actions">
                    <button
                      onClick={() => handleEvaluate(job)}
                      className="btn btn-secondary btn-sm"
                      title="Run 8-Block Matrix Evaluation"
                    >
                      <Target size={13} />
                      <span>Evaluate</span>
                    </button>

                    <Link
                      href="/tailor"
                      className="btn btn-primary btn-sm"
                    >
                      Tailor
                    </Link>

                    <button
                      onClick={() => handleSaveToPipeline(job.id)}
                      className="btn btn-ghost btn-sm"
                      title="Save to tracker"
                    >
                      <BookmarkPlus size={13} />
                      <span>Track</span>
                    </button>

                    {job.source_url && (
                      <a
                        href={job.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-ghost btn-sm"
                        title="Open posting"
                      >
                        <ExternalLink size={13} />
                      </a>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Pagination */}
        {total > 25 && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              gap: '12px',
              marginTop: '24px',
            }}
          >
            <button
              className="btn btn-secondary btn-sm"
              disabled={page <= 1}
              onClick={() => {
                setPage(page - 1);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            >
              <ChevronLeft size={14} />
              <span>Previous</span>
            </button>

            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Page {page} of {Math.ceil(total / 25)}
            </span>

            <button
              className="btn btn-secondary btn-sm"
              disabled={page * 25 >= total}
              onClick={() => {
                setPage(page + 1);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            >
              <span>Next</span>
              <ChevronRight size={14} />
            </button>
          </div>
        )}

        {/* Company Intel Modal */}
        {selectedCompanyIntel && (
          <div className="modal-backdrop" onClick={() => setSelectedCompanyIntel(null)}>
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
                  marginBottom: '14px',
                  borderBottom: '1px solid var(--border-subtle)',
                  paddingBottom: '10px',
                }}
              >
                <div>
                  <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#fff' }}>
                    {selectedCompanyIntel.name}
                  </h2>
                  <span className="badge badge-neutral" style={{ marginTop: '4px' }}>
                    Tier: {selectedCompanyIntel.intel.tier || 'Tech'}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedCompanyIntel(null)}
                  className="btn btn-ghost btn-sm"
                >
                  <X size={16} />
                </button>
              </div>

              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '16px' }}>
                {selectedCompanyIntel.intel.overview}
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '16px' }}>
                <div style={{ background: '#16161a', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Funding</div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#fff' }}>
                    {selectedCompanyIntel.intel.funding_stage || 'N/A'}
                  </div>
                </div>
                <div style={{ background: '#16161a', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Headcount</div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#fff' }}>
                    {selectedCompanyIntel.intel.estimated_headcount || 'N/A'}
                  </div>
                </div>
                <div style={{ background: '#16161a', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Culture</div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#34d399' }}>
                    {selectedCompanyIntel.intel.engineering_culture_rating || 4.0} / 5
                  </div>
                </div>
              </div>

              {selectedCompanyIntel.intel.potential_red_flags && selectedCompanyIntel.intel.potential_red_flags.length > 0 && (
                <div style={{ background: 'rgba(244, 63, 94, 0.08)', border: '1px solid rgba(244, 63, 94, 0.2)', padding: '12px', borderRadius: 'var(--radius-sm)', marginBottom: '16px' }}>
                  <div style={{ fontWeight: 600, color: '#fb7185', fontSize: '0.82rem', marginBottom: '4px' }}>
                    Red flags noted:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {selectedCompanyIntel.intel.potential_red_flags.map((rf, rfi) => (
                      <li key={rfi}>{rf}</li>
                    ))}
                  </ul>
                </div>
              )}

              <button
                onClick={() => setSelectedCompanyIntel(null)}
                className="btn btn-secondary btn-sm"
                style={{ width: '100%' }}
              >
                Close
              </button>
            </div>
          </div>
        )}

        {/* 8-Block Evaluation Modal */}
        {(evalLoading || selectedEval) && (
          <div
            className="modal-backdrop"
            onClick={() => {
              setSelectedEval(null);
              setEvalJob(null);
            }}
          >
            <div
              className="modal-dialog"
              onClick={(e) => e.stopPropagation()}
              style={{ maxWidth: '640px' }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '14px',
                  borderBottom: '1px solid var(--border-subtle)',
                  paddingBottom: '10px',
                }}
              >
                <div>
                  <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#fff' }}>
                    8-Block Matrix Evaluation
                  </h2>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    {evalJob?.title} &middot; {evalJob?.company?.name}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setSelectedEval(null);
                    setEvalJob(null);
                  }}
                  className="btn btn-ghost btn-sm"
                >
                  <X size={16} />
                </button>
              </div>

              {evalLoading ? (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    Analyzing role fit, seniority level, and legitimacy...
                  </p>
                </div>
              ) : selectedEval && (
                <div>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      background: '#16161a',
                      padding: '12px 16px',
                      borderRadius: 'var(--radius-sm)',
                      marginBottom: '16px',
                    }}
                  >
                    <div>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>RECOMMENDATION</span>
                      <div style={{ fontWeight: 600, fontSize: '0.95rem', color: '#34d399' }}>
                        {selectedEval.recommendation || 'APPLY_WITH_TAILORING'}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>FIT SCORE</span>
                      <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#fff' }}>
                        {selectedEval.overall_score || 80}%
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '16px' }}>
                    <div style={{ background: '#16161a', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
                      <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.78rem' }}>Role Match</div>
                      <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        {String((selectedEval.block_a_role_match as Record<string, unknown>)?.summary || 'Aligned')}
                      </p>
                    </div>

                    <div style={{ background: '#16161a', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
                      <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.78rem' }}>CV Overlap</div>
                      <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        {String((selectedEval.block_b_cv_fit as Record<string, unknown>)?.skills_overlap_pct || '65')}% skills match
                      </p>
                    </div>

                    <div style={{ background: '#16161a', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
                      <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.78rem' }}>Level Strategy</div>
                      <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        {String((selectedEval.block_c_level_strategy as Record<string, unknown>)?.strategy_notes || 'Lateral')}
                      </p>
                    </div>

                    <div style={{ background: '#16161a', padding: '10px', borderRadius: 'var(--radius-sm)' }}>
                      <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.78rem' }}>Estimated Median</div>
                      <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        ₹{Number((selectedEval.block_d_compensation as Record<string, unknown>)?.estimated_median || 2000000).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <Link href="/tailor" className="btn btn-primary btn-sm" style={{ flex: 1 }}>
                      Tailor Resume for this Role
                    </Link>
                    <button
                      onClick={() => {
                        setSelectedEval(null);
                        setEvalJob(null);
                      }}
                      className="btn btn-secondary btn-sm"
                    >
                      Close
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
