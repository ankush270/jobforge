'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  applications,
  hasToken,
  jobs,
  resumes,
  type FunnelStats,
  type Job,
  type Resume,
} from '@/lib/api';
import { Topbar } from '@/components/Topbar';
import { Sidebar } from '@/components/Sidebar';
import { useAuth } from '@/lib/auth-context';
import { ScrapeJobsModal } from '@/components/ScrapeJobsModal';
import {
  Send,
  Eye,
  Mic,
  Award,
  TrendingUp,
  Ghost,
  Plus,
  Upload,
  ArrowRight,
  MapPin,
  ChevronRight,
  Briefcase,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<FunnelStats | null>(null);
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [myResumes, setMyResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [scrapeOpen, setScrapeOpen] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    async function loadDashboard() {
      if (!hasToken()) {
        setLoading(false);
        return;
      }
      try {
        const [s, j, r] = await Promise.all([
          applications.stats().catch(() => null),
          jobs.list({ page: 1 }).catch(() => ({ jobs: [] })),
          resumes.list().catch(() => []),
        ]);
        setStats(s);
        setRecentJobs((j as { jobs: Job[] }).jobs?.slice(0, 5) || []);
        setMyResumes(r as Resume[]);
      } catch {
        // Not logged in
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, [user, reloadKey]);

  return (
    <div className="app-shell">
      <Topbar />
      <Sidebar />

      <main className="main-content">
        {/* Hero Header */}
        <div style={{ position: 'relative', zIndex: 1, marginBottom: '28px' }}>
          <div className="page-header">
            <div>
              <div className="page-badge">
                <Briefcase size={12} style={{ color: 'var(--accent)' }} />
                <span>APPLICATION PIPELINE &middot; DIRECT ATS INTELLIGENCE</span>
              </div>
              <h1 className="page-title" style={{ fontSize: '1.9rem', marginTop: '6px' }}>
                Command Center & Pipeline Overview
              </h1>
              <p className="page-subtitle">
                Autonomous scraping, ATS resume tailoring, and real-time application trajectory.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
              <Link href="/resumes" className="btn btn-secondary">
                <Upload size={14} />
                <span>Upload Resume</span>
              </Link>
              <button
                id="dashboard-scrape-jobs"
                className="btn btn-primary"
                onClick={() => setScrapeOpen(true)}
              >
                <Plus size={14} />
                <span>Scrape Jobs</span>
              </button>
            </div>
          </div>
        </div>

        {/* Scrape Modal */}
        <ScrapeJobsModal
          open={scrapeOpen}
          onClose={() => setScrapeOpen(false)}
          onDone={() => setReloadKey((k) => k + 1)}
        />

        {/* 6 Dark Luxury Stat Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-card-header">
              <span className="stat-card-label">Applications Sent</span>
              <div className="stat-card-icon-wrap">
                <Send size={14} />
              </div>
            </div>
            <div className="stat-card-value">{stats?.total_applied ?? 0}</div>
            <div className="stat-card-trend">
              <span style={{ color: 'var(--accent)' }}>Active</span> in pipeline
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-card-header">
              <span className="stat-card-label">In Screening</span>
              <div className="stat-card-icon-wrap">
                <Eye size={14} />
              </div>
            </div>
            <div className="stat-card-value">{stats?.screening ?? 0}</div>
            <div className="stat-card-trend">Recruiter review stage</div>
          </div>

          <div className="stat-card">
            <div className="stat-card-header">
              <span className="stat-card-label">Interview Rounds</span>
              <div className="stat-card-icon-wrap">
                <Mic size={14} />
              </div>
            </div>
            <div className="stat-card-value">{stats?.interviewing ?? 0}</div>
            <div className="stat-card-trend">Active discussions</div>
          </div>

          <div className="stat-card featured">
            <div className="stat-card-header">
              <span className="stat-card-label">Offers Received</span>
              <div className="stat-card-icon-wrap" style={{ borderColor: 'var(--border-accent)' }}>
                <Award size={14} style={{ color: 'var(--accent)' }} />
              </div>
            </div>
            <div className="stat-card-value" style={{ color: 'var(--accent)' }}>
              {stats?.offers ?? 0}
            </div>
            <div className="stat-card-trend" style={{ color: 'var(--accent-bright)' }}>
              Goal milestone
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-card-header">
              <span className="stat-card-label">Response Rate</span>
              <div className="stat-card-icon-wrap">
                <TrendingUp size={14} />
              </div>
            </div>
            <div className="stat-card-value">
              {stats?.screen_rate != null ? `${stats.screen_rate}%` : '—'}
            </div>
            <div className="stat-card-trend">CV conversion efficiency</div>
          </div>

          <div className="stat-card">
            <div className="stat-card-header">
              <span className="stat-card-label">Cold Leads</span>
              <div className="stat-card-icon-wrap">
                <Ghost size={14} />
              </div>
            </div>
            <div className="stat-card-value" style={{ color: '#fb7185' }}>
              {stats?.ghosted ?? 0}
            </div>
            <div className="stat-card-trend">No response &gt; 30d</div>
          </div>
        </div>

        {/* Pipeline Summary Bar */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="card-header">
            <div>
              <h2 className="card-title">Application Funnel Velocity</h2>
              <p className="card-subtitle">Real-time status of your active application pipeline</p>
            </div>
            <Link href="/applications" className="btn btn-secondary btn-sm">
              <span>View Kanban Board</span>
              <ArrowRight size={13} />
            </Link>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
              gap: '10px',
              marginTop: '8px',
            }}
          >
            {[
              { label: 'Saved', count: stats?.saved ?? 0 },
              { label: 'Applied', count: stats?.total_applied ?? 0 },
              { label: 'Screening', count: stats?.screening ?? 0 },
              { label: 'Interviewing', count: stats?.interviewing ?? 0 },
              { label: 'Offers', count: stats?.offers ?? 0 },
            ].map((stage, idx) => (
              <div
                key={stage.label}
                style={{
                  background: 'var(--bg-surface)',
                  borderRadius: 'var(--r-md)',
                  padding: '12px 16px',
                  boxShadow: 'inset 0 1px 0 rgba(255, 248, 230, 0.05)',
                }}
              >
                <div style={{ fontSize: '0.74rem', color: 'var(--text-body)' }}>{stage.label}</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                  {stage.count}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Two Column Layout: Recent Jobs & My Resumes */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
          {/* Recent Jobs */}
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">Recent Opportunities</h2>
                <p className="card-subtitle">Latest scraped listings from top career portals</p>
              </div>
              <Link href="/jobs" className="btn btn-secondary btn-sm">
                <span>View all</span>
                <ChevronRight size={13} />
              </Link>
            </div>

            {recentJobs.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 16px', color: 'var(--text-body)' }}>
                <p style={{ fontSize: '0.88rem' }}>No listings ingested yet.</p>
                <button
                  className="btn btn-primary btn-sm"
                  style={{ marginTop: '12px' }}
                  onClick={() => setScrapeOpen(true)}
                >
                  Scrape jobs now
                </button>
              </div>
            ) : (
              <div className="job-list">
                {recentJobs.map((job) => {
                  const companyInitials = (job.company?.name || 'J').substring(0, 2).toUpperCase();
                  return (
                    <div key={job.id} className="job-card">
                      <div className="job-card-main">
                        <div className="job-card-avatar">{companyInitials}</div>
                        <div className="job-card-content">
                          <div className="job-card-company">
                            <span>{job.company?.name || 'Unknown Company'}</span>
                            {job.is_ghost && <span className="ghost-badge">Ghost</span>}
                          </div>
                          <div className="job-card-title">{job.title}</div>
                          <div className="job-card-meta">
                            {job.location && (
                              <span className="job-meta-item">
                                <MapPin size={11} /> {job.location}
                              </span>
                            )}
                            <span className="badge badge-neutral">{job.source_platform}</span>
                          </div>
                        </div>
                      </div>

                      <div className="job-card-actions">
                        <Link href="/tailor" className="btn btn-secondary btn-sm">
                          Tailor
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* My Resumes */}
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">Master Resumes</h2>
                <p className="card-subtitle">Parsed profiles ready for ATS optimization</p>
              </div>
              <Link href="/resumes" className="btn btn-secondary btn-sm">
                <span>Manage</span>
                <ChevronRight size={13} />
              </Link>
            </div>

            {myResumes.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 16px', color: 'var(--text-body)' }}>
                <p style={{ fontSize: '0.88rem' }}>No master resume uploaded.</p>
                <Link href="/resumes" className="btn btn-secondary btn-sm" style={{ marginTop: '12px' }}>
                  Upload resume
                </Link>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {myResumes.map((r) => (
                  <div
                    key={r.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 14px',
                      background: 'var(--bg-surface)',
                      borderRadius: 'var(--r-md)',
                      boxShadow: 'inset 0 1px 0 rgba(255, 248, 230, 0.05)',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                        {r.filename || 'Master_Resume.pdf'}
                      </div>
                      <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                        {r.is_master ? 'Primary Master' : 'Tailored Variant'} &middot;{' '}
                        {new Date(r.created_at).toLocaleDateString()}
                      </div>
                    </div>

                    <Link href="/tailor" className="btn btn-ghost btn-sm">
                      Tailor
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
