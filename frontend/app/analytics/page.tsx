'use client';

import { useEffect, useState } from 'react';
import { applications, hasToken, type FunnelStats } from '@/lib/api';
import { Topbar } from '@/components/Topbar';
import { Sidebar } from '@/components/Sidebar';
import { useAuth } from '@/lib/auth-context';
import {
  BarChart3,
  TrendingUp,
  Award,
  Ghost,
  Send,
  Lightbulb,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';

export default function AnalyticsPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<FunnelStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      if (!hasToken()) {
        setStats(null);
        setLoading(false);
        return;
      }
      try {
        const data = await applications.stats();
        setStats(data);
      } catch {
        // Not logged in
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, [user]);

  const funnelStages = stats
    ? [
        { label: 'Applied', value: stats.total_applied, color: '#818cf8' },
        { label: 'Screening', value: stats.screening, color: '#38bdf8' },
        { label: 'Interviewing', value: stats.interviewing, color: '#c084fc' },
        { label: 'Offers', value: stats.offers, color: '#34d399' },
        { label: 'Rejected', value: stats.rejected, color: '#f87171' },
        { label: 'Ghosted', value: stats.ghosted, color: '#64748b' },
      ]
    : [];

  const maxValue = Math.max(...funnelStages.map((s) => s.value), 1);

  return (
    <div className="app-shell">
      <Topbar />
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <h1 className="page-title">Performance Analytics</h1>
            <p className="page-subtitle">
              Comprehensive conversion metrics across your job search lifecycle
            </p>
          </div>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
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
            <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Loading analytics metrics...</p>
          </div>
        ) : !stats ? (
          <div className="card" style={{ textAlign: 'center', padding: '80px 40px' }}>
            <BarChart3 size={48} style={{ opacity: 0.3, marginBottom: '16px' }} />
            <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#fff' }}>
              No application metrics recorded
            </h2>
            <p style={{ color: 'var(--text-muted)', marginTop: '8px', maxWidth: '420px', margin: '8px auto 0' }}>
              Start applying to scraped jobs or import existing pipeline roles to generate your conversion funnel.
            </p>
          </div>
        ) : (
          <>
            {/* Key Metrics */}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-card-header">
                  <span className="stat-card-label">Total Applied</span>
                  <div className="stat-card-icon-wrap" style={{ background: 'var(--accent-subtle)', color: 'var(--accent)' }}>
                    <Send size={18} />
                  </div>
                </div>
                <div className="stat-card-value">{stats.total_applied}</div>
                <div className="stat-card-trend">
                  <span style={{ color: 'var(--accent)' }}>Total outreach</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-card-header">
                  <span className="stat-card-label">Screening Rate</span>
                  <div className="stat-card-icon-wrap" style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}>
                    <TrendingUp size={18} />
                  </div>
                </div>
                <div
                  className="stat-card-value"
                  style={{
                    color: stats.screen_rate && stats.screen_rate > 30 ? '#34d399' : '#fbbf24',
                  }}
                >
                  {stats.screen_rate != null ? `${stats.screen_rate}%` : '—'}
                </div>
                <div className="stat-card-trend">
                  <span style={{ color: 'var(--text-muted)' }}>Industry benchmark: 8-12%</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-card-header">
                  <span className="stat-card-label">Offer Rate</span>
                  <div className="stat-card-icon-wrap" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>
                    <Award size={18} />
                  </div>
                </div>
                <div className="stat-card-value" style={{ color: '#34d399' }}>
                  {stats.offer_rate != null ? `${stats.offer_rate}%` : '—'}
                </div>
                <div className="stat-card-trend">
                  <span style={{ color: '#10b981' }}>Offer conversion</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-card-header">
                  <span className="stat-card-label">Ghost Rate</span>
                  <div className="stat-card-icon-wrap" style={{ background: 'rgba(244, 63, 94, 0.15)', color: '#f43f5e' }}>
                    <Ghost size={18} />
                  </div>
                </div>
                <div
                  className="stat-card-value"
                  style={{ color: stats.ghosted > 5 ? 'var(--error)' : 'var(--text-primary)' }}
                >
                  {stats.total_applied > 0
                    ? `${((stats.ghosted / stats.total_applied) * 100).toFixed(0)}%`
                    : '—'}
                </div>
                <div className="stat-card-trend">
                  <span style={{ color: 'var(--text-muted)' }}>Unresponsive postings</span>
                </div>
              </div>
            </div>

            {/* Funnel Visualization */}
            <div className="card" style={{ marginBottom: '28px' }}>
              <div className="card-header">
                <div>
                  <h2 className="card-title">
                    <BarChart3 size={18} style={{ color: 'var(--accent)' }} />
                    <span>Application Conversion Funnel</span>
                  </h2>
                  <p className="card-subtitle">Volume distribution across pipeline milestones</p>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '16px' }}>
                {funnelStages.map(({ label, value, color }) => (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <span
                      style={{
                        width: '110px',
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        color: 'var(--text-secondary)',
                        textAlign: 'right',
                      }}
                    >
                      {label}
                    </span>
                    <div
                      style={{
                        flex: 1,
                        height: '36px',
                        background: 'var(--bg-surface)',
                        borderRadius: 'var(--radius-md)',
                        overflow: 'hidden',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div
                        style={{
                          width: `${(value / maxValue) * 100}%`,
                          height: '100%',
                          background: color,
                          borderRadius: 'var(--radius-md)',
                          transition: 'width 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
                          minWidth: value > 0 ? '36px' : '0',
                          display: 'flex',
                          alignItems: 'center',
                          paddingLeft: '14px',
                          fontSize: '0.85rem',
                          fontWeight: 700,
                          color: 'white',
                          boxShadow: value > 0 ? `0 0 15px ${color}44` : 'none',
                        }}
                      >
                        {value > 0 ? value : ''}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Strategic Insights */}
            <div className="card">
              <div className="card-header">
                <div>
                  <h2 className="card-title">
                    <Lightbulb size={18} style={{ color: '#fbbf24' }} />
                    <span>AI Strategic Observations</span>
                  </h2>
                  <p className="card-subtitle">Real-time diagnosis based on your conversion funnel</p>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {stats.screen_rate != null && stats.screen_rate < 15 && (
                  <div
                    style={{
                      padding: '14px 18px',
                      background: 'rgba(245, 158, 11, 0.08)',
                      borderLeft: '4px solid #f59e0b',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.9rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                    }}
                  >
                    <AlertTriangle size={20} style={{ color: '#fbbf24', flexShrink: 0 }} />
                    <div>
                      <strong style={{ color: '#fff' }}>Screen rate currently below optimal ({stats.screen_rate}%).</strong>{' '}
                      <span style={{ color: 'var(--text-secondary)' }}>
                        Tailor your resume bullets to directly mirror the job specifications and ATS keywords before submitting.
                      </span>
                    </div>
                  </div>
                )}

                {stats.ghosted > 0 && (
                  <div
                    style={{
                      padding: '14px 18px',
                      background: 'rgba(244, 63, 94, 0.08)',
                      borderLeft: '4px solid #f43f5e',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.9rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                    }}
                  >
                    <Ghost size={20} style={{ color: '#fb7185', flexShrink: 0 }} />
                    <div>
                      <strong style={{ color: '#fff' }}>{stats.ghosted} applications detected as ghost postings.</strong>{' '}
                      <span style={{ color: 'var(--text-secondary)' }}>
                        Use our automated Ghost Detector to scan repost frequencies and avoid inactive job vacancies.
                      </span>
                    </div>
                  </div>
                )}

                {stats.offers > 0 && (
                  <div
                    style={{
                      padding: '14px 18px',
                      background: 'rgba(16, 185, 129, 0.08)',
                      borderLeft: '4px solid #10b981',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.9rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                    }}
                  >
                    <CheckCircle2 size={20} style={{ color: '#34d399', flexShrink: 0 }} />
                    <div>
                      <strong style={{ color: '#fff' }}>{stats.offers} job offer(s) recorded!</strong>{' '}
                      <span style={{ color: 'var(--text-secondary)' }}>
                        Consult the Salary Intel Copilot to benchmark equity, bonuses, and negotiate competitive compensation.
                      </span>
                    </div>
                  </div>
                )}

                {stats.total_applied === 0 && (
                  <div
                    style={{
                      padding: '14px 18px',
                      background: 'var(--accent-subtle)',
                      borderLeft: '4px solid var(--accent)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.9rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                    }}
                  >
                    <TrendingUp size={20} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                    <div>
                      <strong style={{ color: 'var(--text-primary)' }}>Initialize Your Pipeline</strong>{' '}
                      <span style={{ color: 'var(--text-secondary)' }}>
                        Upload your master resume, trigger a verified board scan, and begin tracking direct applications.
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
