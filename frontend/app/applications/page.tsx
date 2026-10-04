'use client';

import { useEffect, useState } from 'react';
import {
  applications,
  hasToken,
  type Application,
  type KanbanBoard,
} from '@/lib/api';
import { Topbar } from '@/components/Topbar';
import { Sidebar } from '@/components/Sidebar';
import { useAuth } from '@/lib/auth-context';
import {
  Layers,
  MapPin,
  Calendar,
  Building2,
  CheckCircle2,
  XCircle,
  Award,
  ChevronRight,
  Bookmark,
  Send,
  Eye,
  Mic,
  Ghost,
} from 'lucide-react';

const KANBAN_COLUMNS = [
  { key: 'saved', label: 'Saved', icon: Bookmark, color: '#94a3b8' },
  { key: 'ready', label: 'Ready to Apply', icon: CheckCircle2, color: '#38bdf8' },
  { key: 'applied', label: 'Applied', icon: Send, color: '#818cf8' },
  { key: 'screening', label: 'Screening', icon: Eye, color: '#fbbf24' },
  { key: 'interview_scheduled', label: 'Interviews', icon: Mic, color: '#c084fc' },
  { key: 'offer_received', label: 'Offers', icon: Award, color: '#34d399' },
  { key: 'rejected', label: 'Archived', icon: XCircle, color: '#f87171' },
  { key: 'ghosted', label: 'Ghosted', icon: Ghost, color: '#fda4af' },
];

export default function ApplicationsPage() {
  const { user } = useAuth();
  const [board, setBoard] = useState<KanbanBoard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadBoard() {
      if (!hasToken()) {
        setBoard(null);
        setLoading(false);
        return;
      }
      try {
        const data = await applications.board();
        setBoard(data);
      } catch {
        // Handle auth error
      } finally {
        setLoading(false);
      }
    }
    loadBoard();
  }, [user]);

  const handleStatusChange = async (appId: string, newStatus: string) => {
    try {
      await applications.update(appId, { status: newStatus } as Partial<Application>);
      const data = await applications.board();
      setBoard(data);
    } catch (e) {
      console.error('Failed to update status', e);
    }
  };

  const totalApps = board ? Object.values(board.stats).reduce((a, b) => a + b, 0) : 0;

  return (
    <div className="app-shell">
      <Topbar />
      <Sidebar />

      <main className="main-content fluid">
        {/* Ambient Dark Luxury Orb */}
        <div className="hero-orb" />

        <div className="page-header">
          <div>
            <div className="page-badge">
              <span>PIPELINE TRACKER</span>
            </div>
            <h1 className="page-title" style={{ marginTop: '6px' }}>
              Application Kanban Board
            </h1>
            <p className="page-subtitle">
              {totalApps} active opportunities tracked across every interview and offer checkpoint.
            </p>
          </div>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '80px', color: 'var(--text-body)' }}>
            <div
              style={{
                display: 'inline-block',
                width: '36px',
                height: '36px',
                border: '3px solid rgba(212, 160, 60, 0.2)',
                borderTopColor: 'var(--accent)',
                borderRadius: '50%',
                animation: 'spin 0.8s linear infinite',
                marginBottom: '16px',
              }}
            />
            <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Loading Kanban Pipeline...</p>
          </div>
        ) : (
          <div className="kanban-board">
            {KANBAN_COLUMNS.map(({ key, label, icon: Icon, color }) => {
              const cards = board?.columns[key] || [];
              const count = board?.stats[key] || 0;

              return (
                <div key={key} className="kanban-column">
                  <div className="kanban-column-header">
                    <span className="kanban-column-title">
                      <Icon size={16} style={{ color }} />
                      <span>{label}</span>
                    </span>
                    <span className="kanban-column-count">{count}</span>
                  </div>

                  {cards.length === 0 ? (
                    <div
                      style={{
                        textAlign: 'center',
                        padding: '36px 12px',
                        color: 'var(--text-muted)',
                        fontSize: '0.82rem',
                        border: '1px dashed var(--border-subtle)',
                        borderRadius: 'var(--radius-md)',
                        margin: '8px 0',
                      }}
                    >
                      Empty stage
                    </div>
                  ) : (
                    cards.map((app) => {
                      const companyInitials = (app.job?.company?.name || 'CO').substring(0, 2).toUpperCase();

                      return (
                        <div key={app.id} className="kanban-card">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                            <div
                              style={{
                                width: '26px',
                                height: '26px',
                                borderRadius: '6px',
                                background: 'rgba(255, 255, 255, 0.08)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '0.7rem',
                                fontWeight: 700,
                                color: '#a5b4fc',
                              }}
                            >
                              {companyInitials}
                            </div>
                            <span className="kanban-card-company" style={{ margin: 0 }}>
                              {app.job?.company?.name || 'Company'}
                            </span>
                          </div>

                          <div className="kanban-card-title">
                            {app.job?.title || 'Target Role'}
                          </div>

                          <div className="kanban-card-meta">
                            {app.job?.location && (
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                                <MapPin size={11} /> {app.job.location}
                              </span>
                            )}
                            {app.applied_at && (
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                                <Calendar size={11} /> {new Date(app.applied_at).toLocaleDateString()}
                              </span>
                            )}
                          </div>

                          {/* Quick Stage Actions */}
                          <div style={{ display: 'flex', gap: '6px', marginTop: '14px', flexWrap: 'wrap', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
                            {key === 'saved' && (
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                                onClick={() => handleStatusChange(app.id, 'ready')}
                              >
                                <span>Mark Ready</span>
                                <ChevronRight size={12} />
                              </button>
                            )}

                            {key === 'ready' && (
                              <button
                                className="btn btn-primary btn-sm"
                                style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                                onClick={() => handleStatusChange(app.id, 'applied')}
                              >
                                <span>Applied</span>
                                <Send size={11} />
                              </button>
                            )}

                            {key === 'applied' && (
                              <>
                                <button
                                  className="btn btn-secondary btn-sm"
                                  style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                                  onClick={() => handleStatusChange(app.id, 'screening')}
                                >
                                  <span>Screening</span>
                                  <ChevronRight size={12} />
                                </button>
                                <button
                                  className="btn btn-ghost btn-sm"
                                  style={{ fontSize: '0.72rem', padding: '3px 8px', color: '#f87171' }}
                                  onClick={() => handleStatusChange(app.id, 'rejected')}
                                >
                                  Reject
                                </button>
                              </>
                            )}

                            {key === 'screening' && (
                              <button
                                className="btn btn-primary btn-sm"
                                style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                                onClick={() => handleStatusChange(app.id, 'interview_scheduled')}
                              >
                                <span>Interview</span>
                                <Mic size={11} />
                              </button>
                            )}

                            {key === 'interview_scheduled' && (
                              <>
                                <button
                                  className="btn btn-primary btn-sm"
                                  style={{
                                    fontSize: '0.72rem',
                                    padding: '3px 8px',
                                    background: 'var(--gradient-success)',
                                  }}
                                  onClick={() => handleStatusChange(app.id, 'offer_received')}
                                >
                                  <span>Offer!</span>
                                  <Award size={11} />
                                </button>
                                <button
                                  className="btn btn-ghost btn-sm"
                                  style={{ fontSize: '0.72rem', padding: '3px 8px', color: '#f87171' }}
                                  onClick={() => handleStatusChange(app.id, 'rejected')}
                                >
                                  Reject
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
