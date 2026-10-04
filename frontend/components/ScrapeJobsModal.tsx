'use client';

import { useState } from 'react';
import { jobs } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { X } from 'lucide-react';

const PLATFORMS = [
  { id: 'linkedin', label: 'LinkedIn' },
  { id: 'indeed', label: 'Indeed' },
  { id: 'glassdoor', label: 'Glassdoor' },
  { id: 'hacker_news', label: 'Hacker News' },
  { id: 'greenhouse', label: 'Greenhouse' },
  { id: 'lever', label: 'Lever' },
  { id: 'google', label: 'Google Jobs' },
];

export function ScrapeJobsModal({
  open,
  onClose,
  onDone,
}: {
  open: boolean;
  onClose: () => void;
  onDone?: () => void;
}) {
  const { user, openAuthModal } = useAuth();
  const [query, setQuery] = useState('Software Engineer');
  const [location, setLocation] = useState('India');
  const [platforms, setPlatforms] = useState<string[]>(['linkedin', 'indeed']);
  const [count, setCount] = useState(20);
  const [scanTargetCompanies, setScanTargetCompanies] = useState(true);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const toggle = (id: string) =>
    setPlatforms((p) =>
      p.includes(id) ? p.filter((x) => x !== id) : [...p, id]
    );

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      onClose();
      openAuthModal('login');
      return;
    }
    if (!query.trim() || platforms.length === 0) {
      setError('Please provide a query and pick at least one platform.');
      return;
    }
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await jobs.scrape({
        search_query: query.trim(),
        location: location.trim() || undefined,
        platforms,
        results_wanted: count,
        scan_target_companies: scanTargetCompanies,
      });
      setResult(res.message);
      onDone?.();
    } catch (err) {
      setError((err as Error).message || 'Scraping failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={busy ? undefined : onClose}>
      <form
        onClick={(e) => e.stopPropagation()}
        onSubmit={submit}
        className="modal-dialog"
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
            borderBottom: '1px solid var(--border-subtle)',
            paddingBottom: '12px',
          }}
        >
          <div>
            <h2 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#fff' }}>
              Scrape Postings
            </h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Fetch listings from external job boards & ATS portals
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="btn btn-ghost btn-sm"
          >
            <X size={15} />
          </button>
        </div>

        <div style={{ marginBottom: '12px' }}>
          <label className="label">Role / Keyword</label>
          <input
            id="scrape-query"
            className="input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={busy}
          />
        </div>

        <div style={{ marginBottom: '14px' }}>
          <label className="label">Location</label>
          <input
            id="scrape-location"
            className="input"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            disabled={busy}
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label className="label">Platforms</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {PLATFORMS.map((p) => {
              const isSelected = platforms.includes(p.id);
              return (
                <button
                  type="button"
                  key={p.id}
                  id={`scrape-platform-${p.id}`}
                  disabled={busy}
                  onClick={() => toggle(p.id)}
                  className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.78rem' }}
                >
                  {p.label}
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Results per platform:
          </span>
          <input
            id="scrape-count"
            type="number"
            min={5}
            max={50}
            className="input"
            style={{ width: '70px', textAlign: 'center' }}
            value={count}
            onChange={(e) => setCount(Number(e.target.value))}
            disabled={busy}
          />
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            marginBottom: '18px',
            padding: '10px 12px',
            borderRadius: '8px',
            background: 'rgba(230, 81, 0, 0.08)',
            border: '1px solid rgba(230, 81, 0, 0.25)',
          }}
        >
          <input
            id="scrape-target-companies"
            type="checkbox"
            checked={scanTargetCompanies}
            onChange={(e) => setScanTargetCompanies(e.target.checked)}
            disabled={busy}
            style={{ width: '16px', height: '16px', cursor: 'pointer', accentColor: 'var(--accent)' }}
          />
          <label
            htmlFor="scrape-target-companies"
            style={{ fontSize: '0.8rem', color: '#fff', cursor: 'pointer', userSelect: 'none' }}
          >
            🎯 <strong>Scan 290+ Target Company Portals</strong> (Greenhouse, Lever, Ashby)
          </label>
        </div>

        {busy && (
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Scraping live listings... please wait.
          </p>
        )}
        {result && (
          <p style={{ fontSize: '0.82rem', color: '#34d399', marginBottom: '12px' }}>
            ✓ {result}
          </p>
        )}
        {error && (
          <p style={{ fontSize: '0.82rem', color: '#fb7185', marginBottom: '12px' }}>
            ✕ {error}
          </p>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button
            type="button"
            id="scrape-close"
            className="btn btn-secondary btn-sm"
            onClick={onClose}
            disabled={busy}
          >
            {result ? 'Done' : 'Cancel'}
          </button>
          <button
            type="submit"
            id="scrape-submit"
            className="btn btn-primary btn-sm"
            disabled={busy}
          >
            {busy ? 'Scraping...' : 'Start Scrape'}
          </button>
        </div>
      </form>
    </div>
  );
}
