'use client';

import { useState } from 'react';
import { Topbar } from '@/components/Topbar';
import { Sidebar } from '@/components/Sidebar';
import { salaries, type SalaryBenchmarkResult } from '@/lib/api';
import {
  DollarSign,
  TrendingUp,
  Award,
  Sparkles,
  Copy,
  Check,
  Building2,
  Briefcase,
  Layers,
  FileText,
} from 'lucide-react';

export default function SalaryIntelPage() {
  const [role, setRole] = useState('Senior Software Engineer');
  const [experienceYrs, setExperienceYrs] = useState<number>(5);
  const [location, setLocation] = useState('India');
  const [currency, setCurrency] = useState('INR');
  const [offeredSalary, setOfferedSalary] = useState<number>(2500000);
  const [companyName, setCompanyName] = useState('Target Tech Co');

  const [benchmark, setBenchmark] = useState<SalaryBenchmarkResult | null>(null);
  const [gapAnalysis, setGapAnalysis] = useState<Record<string, unknown> | null>(null);
  const [negotiationScript, setNegotiationScript] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [negLoading, setNegLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleAnalyze() {
    setLoading(true);
    try {
      const res = await salaries.analyzeGap({
        role,
        experience_yrs: experienceYrs,
        location,
        currency,
        offered_salary: offeredSalary,
      });
      setBenchmark(res.benchmark);
      setGapAnalysis(res.analysis);
    } catch (err: unknown) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateScript() {
    if (!benchmark) return;
    setNegLoading(true);
    try {
      const res = await salaries.negotiate({
        company_name: companyName,
        role,
        current_offer: offeredSalary,
        target_salary: benchmark.p75,
        currency,
        key_strengths: [
          'Full-stack architecture & distributed systems',
          'High throughput latency optimization',
          'Cross-functional engineering mentorship',
        ],
      });
      setNegotiationScript(res.negotiation_script);
    } catch (err: unknown) {
      console.error(err);
    } finally {
      setNegLoading(false);
    }
  }

  const handleCopy = () => {
    if (!negotiationScript) return;
    navigator.clipboard.writeText(negotiationScript);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="app-shell">
      <Topbar />
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <h1 className="page-title">Salary Intelligence & Counter-Offer Copilot</h1>
            <p className="page-subtitle">
              Verified market percentiles, compensation gap calculation, and persuasive counter-offer generator
            </p>
          </div>
        </div>

        {/* Input Panel */}
        <div className="card" style={{ marginBottom: '28px' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
              marginBottom: '20px',
            }}
          >
            <div>
              <label className="label">Target Role</label>
              <input
                className="input"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="e.g. Lead Frontend Engineer"
              />
            </div>
            <div>
              <label className="label">Experience (Years)</label>
              <input
                type="number"
                className="input"
                value={experienceYrs}
                onChange={(e) => setExperienceYrs(Number(e.target.value))}
              />
            </div>
            <div>
              <label className="label">Currency</label>
              <select
                className="select"
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
              >
                <option value="INR">INR (₹)</option>
                <option value="USD">USD ($)</option>
              </select>
            </div>
            <div>
              <label className="label">Offered Base Salary</label>
              <input
                type="number"
                className="input"
                value={offeredSalary}
                onChange={(e) => setOfferedSalary(Number(e.target.value))}
              />
            </div>
          </div>

          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="btn btn-primary"
            style={{ padding: '11px 24px' }}
          >
            <TrendingUp size={16} />
            <span>{loading ? 'Calculating Market Benchmarks...' : 'Analyze Market Gap & Percentiles'}</span>
          </button>
        </div>

        {/* Results Grid */}
        {benchmark && gapAnalysis && (
          <div>
            {/* Percentile Cards */}
            <div className="stats-grid" style={{ marginBottom: '28px' }}>
              <div className="stat-card">
                <div className="stat-card-header">
                  <span className="stat-card-label">25th Percentile</span>
                </div>
                <div className="stat-card-value" style={{ fontSize: '1.5rem', color: '#94a3b8' }}>
                  {currency} {benchmark.p25.toLocaleString()}
                </div>
                <div className="stat-card-trend">
                  <span>Entry/Junior band</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-card-header">
                  <span className="stat-card-label">Market Median (P50)</span>
                </div>
                <div className="stat-card-value" style={{ fontSize: '1.5rem', color: '#818cf8' }}>
                  {currency} {benchmark.p50_median.toLocaleString()}
                </div>
                <div className="stat-card-trend">
                  <span style={{ color: '#818cf8' }}>Standard baseline</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-card-header">
                  <span className="stat-card-label">Target Range (P75)</span>
                </div>
                <div className="stat-card-value" style={{ fontSize: '1.5rem', color: '#34d399' }}>
                  {currency} {benchmark.p75.toLocaleString()}
                </div>
                <div className="stat-card-trend">
                  <span style={{ color: '#34d399' }}>Optimal target offer</span>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-card-header">
                  <span className="stat-card-label">Top Tier (P90)</span>
                </div>
                <div className="stat-card-value" style={{ fontSize: '1.5rem', color: '#f59e0b' }}>
                  {currency} {benchmark.p90.toLocaleString()}
                </div>
                <div className="stat-card-trend">
                  <span style={{ color: '#fbbf24' }}>FAANG/High-tier ceiling</span>
                </div>
              </div>
            </div>

            {/* Strategic Advice Card */}
            <div
              className="card"
              style={{
                padding: '24px',
                marginBottom: '28px',
                borderLeft: '4px solid #10b981',
              }}
            >
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, marginBottom: '8px', color: '#fff' }}>
                Strategic Position: {(gapAnalysis.leverage_status as string || '').replace('_', ' ').toUpperCase()}
              </h3>
              <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.6 }}>
                {gapAnalysis.strategic_advice as string}
              </p>
              <div
                style={{
                  background: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid rgba(16, 185, 129, 0.25)',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.88rem',
                  color: '#34d399',
                }}
              >
                3-Year Projected Cumulative Upside at Target (P75):{' '}
                <strong style={{ color: '#fff', fontSize: '1rem' }}>
                  {currency} {Number(gapAnalysis.three_year_difference_at_p75 || 0).toLocaleString()}
                </strong>
              </div>
            </div>

            {/* Negotiation Generator */}
            <div className="card">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '18px',
                  borderBottom: '1px solid var(--border-subtle)',
                  paddingBottom: '14px',
                  flexWrap: 'wrap',
                  gap: '12px',
                }}
              >
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff' }}>
                    Personalized Counter-Offer Script
                  </h3>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Tactical, non-combative script crafted for HR and engineering directors
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {negotiationScript && (
                    <button onClick={handleCopy} className="btn btn-secondary btn-sm">
                      {copied ? <Check size={14} /> : <Copy size={14} />}
                      <span>{copied ? 'Copied' : 'Copy Script'}</span>
                    </button>
                  )}
                  <button
                    onClick={handleGenerateScript}
                    disabled={negLoading}
                    className="btn btn-primary btn-sm"
                  >
                    <Sparkles size={14} />
                    <span>{negLoading ? 'Drafting Script...' : 'Generate Counter-Offer Script'}</span>
                  </button>
                </div>
              </div>

              {negotiationScript ? (
                <textarea
                  className="textarea"
                  rows={11}
                  value={negotiationScript}
                  onChange={(e) => setNegotiationScript(e.target.value)}
                  style={{ lineHeight: 1.6, fontSize: '0.9rem' }}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 16px', color: 'var(--text-muted)' }}>
                  <FileText size={36} style={{ opacity: 0.3, marginBottom: '8px' }} />
                  <p style={{ fontSize: '0.88rem' }}>
                    Click &ldquo;Generate Counter-Offer Script&rdquo; to auto-compose a respectful, high-leverage compensation email.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
