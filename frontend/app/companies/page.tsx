'use client';

import { useEffect, useState, useMemo, useCallback } from 'react';
import Link from 'next/link';
import { Topbar } from '@/components/Topbar';
import { Sidebar } from '@/components/Sidebar';
import {
  targetCompanies,
  type TargetCompany,
} from '@/lib/api';
import {
  Building2,
  Search,
  ExternalLink,
  Plus,
  X,
  MapPin,
  ShieldCheck,
  Layers,
  ArrowUpRight,
  Filter,
  Trash2,
  Globe,
  Cpu,
  Briefcase,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from 'lucide-react';

const CATEGORIES = [
  'All',
  'Tech / Product',
  'Indian Startups / Unicorns',
  'Trading / Quant',
  'Product / Big Tech',
  'Fintech / Payments',
  'Banking / Finance Tech',
  'Semiconductor / Hardware',
  'Core Engineering / Hardware',
  'AI / ML',
  'Cloud / Security',
  'Enterprise Software',
  'E-commerce / Consumer',
  'Others',
];

const CATEGORY_ICONS: Record<string, string> = {
  'All': '🌐',
  'Tech / Product': '💻',
  'Indian Startups / Unicorns': '🚀',
  'Trading / Quant': '📊',
  'Product / Big Tech': '🏢',
  'Fintech / Payments': '💳',
  'Banking / Finance Tech': '🏦',
  'Semiconductor / Hardware': '🔧',
  'Core Engineering / Hardware': '⚙️',
  'AI / ML': '🤖',
  'Cloud / Security': '🛡️',
  'Enterprise Software': '📦',
  'E-commerce / Consumer': '🛒',
  'Others': '📋',
};

function getAtsBadgeClass(ats: string | null): string {
  if (!ats) return 'ats-badge-unknown';
  const low = ats.toLowerCase();
  if (low.includes('greenhouse')) return 'ats-badge-greenhouse';
  if (low.includes('ashby')) return 'ats-badge-ashby';
  if (low.includes('lever')) return 'ats-badge-lever';
  if (low.includes('workday')) return 'ats-badge-workday';
  return 'ats-badge-direct';
}

function getAtsBadgeLabel(ats: string | null): string {
  if (!ats) return 'Unknown';
  return ats;
}

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<TargetCompany[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  const [addOpen, setAddOpen] = useState(false);
  const [addForm, setAddForm] = useState({ name: '', careers_url: '', category: 'Tech / Product' });
  const [addError, setAddError] = useState('');
  const [addLoading, setAddLoading] = useState(false);
  const [removeLoading, setRemoveLoading] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchCompanies = useCallback(async () => {
    setLoading(true);
    try {
      const data = await targetCompanies.list();
      setCompanies(data);
    } catch {
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  // Show toast with auto-dismiss
  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 3500);
  };

  // Filtered companies
  const filtered = useMemo(() => {
    let result = companies;
    if (activeCategory !== 'All') {
      result = result.filter((c) =>
        c.category.toLowerCase().includes(activeCategory.toLowerCase())
      );
    }
    if (search.trim()) {
      const s = search.toLowerCase();
      result = result.filter(
        (c) =>
          c.name.toLowerCase().includes(s) ||
          c.category.toLowerCase().includes(s) ||
          (c.ats_or_portal || '').toLowerCase().includes(s)
      );
    }
    return result;
  }, [companies, activeCategory, search]);

  // Category counts
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { All: companies.length };
    for (const c of companies) {
      for (const cat of CATEGORIES) {
        if (cat === 'All') continue;
        if (c.category.toLowerCase().includes(cat.toLowerCase())) {
          counts[cat] = (counts[cat] || 0) + 1;
        }
      }
    }
    return counts;
  }, [companies]);

  // ATS distribution
  const atsDistribution = useMemo(() => {
    const dist: Record<string, number> = {};
    for (const c of companies) {
      const key = c.ats_or_portal || 'Unknown';
      dist[key] = (dist[key] || 0) + 1;
    }
    return Object.entries(dist)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);
  }, [companies]);

  // Add company handler
  const handleAdd = async () => {
    if (!addForm.name.trim() || !addForm.careers_url.trim()) {
      setAddError('Name and Careers URL are required');
      return;
    }
    setAddLoading(true);
    setAddError('');
    try {
      await targetCompanies.add(addForm);
      showToast('success', `${addForm.name} added to target list`);
      setAddOpen(false);
      setAddForm({ name: '', careers_url: '', category: 'Tech / Product' });
      fetchCompanies();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to add company';
      setAddError(msg);
    } finally {
      setAddLoading(false);
    }
  };

  // Remove company handler
  const handleRemove = async (name: string) => {
    setRemoveLoading(name);
    try {
      await targetCompanies.remove(name);
      showToast('success', `${name} removed from target list`);
      fetchCompanies();
    } catch {
      showToast('error', `Failed to remove ${name}`);
    } finally {
      setRemoveLoading(null);
    }
  };

  return (
    <div className="app-shell">
      <Topbar />
      <Sidebar />

      <main className="main-content">
        {/* Page Header */}
        <div style={{ position: 'relative', zIndex: 1, marginBottom: '28px' }}>
          <div className="page-header">
            <div>
              <div className="page-badge">
                <Building2 size={12} style={{ color: 'var(--accent)' }} />
                <span>TARGET COMPANIES DIRECTORY · {companies.length} TRACKED</span>
              </div>
              <h1 className="page-title">
                Company <span className="title-accent">Directory</span>
              </h1>
              <p className="page-subtitle">
                290+ pre-filtered career portals with ATS detection — search, browse, and manage your target companies
              </p>
            </div>
            <button
              className="btn-primary"
              onClick={() => setAddOpen(true)}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Plus size={14} />
              Add Company
            </button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="tc-stats-row">
          <div className="tc-stat-card">
            <div className="tc-stat-icon" style={{ background: 'var(--accent-glow)' }}>
              <Building2 size={16} style={{ color: 'var(--accent)' }} />
            </div>
            <div className="tc-stat-info">
              <span className="tc-stat-value">{companies.length}</span>
              <span className="tc-stat-label">Total Companies</span>
            </div>
          </div>
          <div className="tc-stat-card">
            <div className="tc-stat-icon" style={{ background: 'var(--success-glow)' }}>
              <ShieldCheck size={16} style={{ color: 'var(--success)' }} />
            </div>
            <div className="tc-stat-info">
              <span className="tc-stat-value">{companies.filter(c => c.status === 'verified').length}</span>
              <span className="tc-stat-label">Verified Portals</span>
            </div>
          </div>
          <div className="tc-stat-card">
            <div className="tc-stat-icon" style={{ background: 'rgba(59,130,246,0.15)' }}>
              <Cpu size={16} style={{ color: 'var(--info)' }} />
            </div>
            <div className="tc-stat-info">
              <span className="tc-stat-value">{atsDistribution.length}</span>
              <span className="tc-stat-label">ATS Platforms</span>
            </div>
          </div>
          <div className="tc-stat-card">
            <div className="tc-stat-icon" style={{ background: 'rgba(139,92,246,0.15)' }}>
              <Sparkles size={16} style={{ color: '#8b5cf6' }} />
            </div>
            <div className="tc-stat-info">
              <span className="tc-stat-value">{Object.keys(categoryCounts).length - 1}</span>
              <span className="tc-stat-label">Categories</span>
            </div>
          </div>
        </div>

        {/* ATS Distribution Bar */}
        <div className="tc-ats-bar">
          <div className="tc-ats-bar-header">
            <span className="tc-ats-bar-title">
              <Layers size={13} style={{ color: 'var(--accent)' }} />
              ATS Platform Distribution
            </span>
          </div>
          <div className="tc-ats-chips">
            {atsDistribution.map(([name, count]) => (
              <div key={name} className={`tc-ats-chip ${getAtsBadgeClass(name)}`}>
                <span className="tc-ats-chip-name">{name}</span>
                <span className="tc-ats-chip-count">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Search + Category Filter */}
        <div className="tc-controls">
          <div className="tc-search-box">
            <Search size={15} className="tc-search-icon" />
            <input
              type="text"
              placeholder="Search companies, categories, or ATS type..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="tc-search-input"
            />
            {search && (
              <button className="tc-search-clear" onClick={() => setSearch('')}>
                <X size={13} />
              </button>
            )}
          </div>
          <div className="tc-filter-pill-row">
            <Filter size={13} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                className={`tc-filter-pill ${activeCategory === cat ? 'active' : ''}`}
                onClick={() => setActiveCategory(cat)}
              >
                <span className="tc-filter-pill-emoji">{CATEGORY_ICONS[cat] || '📋'}</span>
                {cat}
                {categoryCounts[cat] !== undefined && (
                  <span className="tc-filter-pill-count">{categoryCounts[cat] || 0}</span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Results Count */}
        <div className="tc-results-bar">
          <span className="tc-results-count">
            Showing <strong>{filtered.length}</strong> of {companies.length} companies
            {activeCategory !== 'All' && (
              <span className="tc-results-filter-tag">
                {CATEGORY_ICONS[activeCategory]} {activeCategory}
                <button onClick={() => setActiveCategory('All')} className="tc-results-filter-clear">
                  <X size={11} />
                </button>
              </span>
            )}
          </span>
        </div>

        {/* Companies Grid */}
        {loading ? (
          <div className="tc-loading">
            <div className="tc-loading-spinner" />
            <span>Loading target companies...</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="tc-empty">
            <Building2 size={40} style={{ color: 'var(--text-muted)', marginBottom: '12px' }} />
            <h3>No companies found</h3>
            <p>Try adjusting your search or filter criteria</p>
          </div>
        ) : (
          <div className="tc-grid">
            {filtered.map((company) => (
              <div key={company.name} className="tc-card">
                <div className="tc-card-header">
                  <div className="tc-card-logo">
                    {company.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="tc-card-title-block">
                    <h3 className="tc-card-name">{company.name}</h3>
                    <span className="tc-card-category">{company.category}</span>
                  </div>
                  <div className="tc-card-actions">
                    <button
                      className="tc-card-action-btn tc-card-action-remove"
                      title="Remove from targets"
                      onClick={() => handleRemove(company.name)}
                      disabled={removeLoading === company.name}
                    >
                      {removeLoading === company.name ? (
                        <div className="tc-mini-spinner" />
                      ) : (
                        <Trash2 size={13} />
                      )}
                    </button>
                  </div>
                </div>

                <div className="tc-card-badges">
                  <span className={`tc-ats-badge ${getAtsBadgeClass(company.ats_or_portal)}`}>
                    <Cpu size={10} />
                    {getAtsBadgeLabel(company.ats_or_portal)}
                  </span>
                  {company.status === 'verified' && (
                    <span className="tc-verified-badge">
                      <CheckCircle2 size={10} />
                      Verified
                    </span>
                  )}
                </div>

                {company.locations_in_india.length > 0 && (
                  <div className="tc-card-locations">
                    <MapPin size={11} className="tc-loc-icon" />
                    <span>{company.locations_in_india.slice(0, 3).join(' · ')}</span>
                    {company.locations_in_india.length > 3 && (
                      <span className="tc-loc-more">+{company.locations_in_india.length - 3}</span>
                    )}
                  </div>
                )}

                <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                  <Link
                    href={`/jobs?search=${encodeURIComponent(company.name)}`}
                    className="tc-card-link"
                    style={{ flex: 1, textAlign: 'center', justifyContent: 'center' }}
                  >
                    <Briefcase size={12} />
                    View Jobs
                  </Link>
                  <a
                    href={company.careers_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="tc-card-link"
                    style={{ flex: 1, textAlign: 'center', justifyContent: 'center' }}
                  >
                    <Globe size={12} />
                    Portal
                    <ArrowUpRight size={12} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Add Company Modal */}
      {addOpen && (
        <div className="modal-backdrop" onClick={() => setAddOpen(false)}>
          <div className="modal-panel tc-add-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">
                <Plus size={16} style={{ color: 'var(--accent)' }} />
                Add Target Company
              </h2>
              <button className="modal-close-btn" onClick={() => setAddOpen(false)}>
                <X size={16} />
              </button>
            </div>

            <div className="modal-body">
              <div className="tc-form-group">
                <label className="tc-form-label">Company Name</label>
                <input
                  type="text"
                  className="tc-form-input"
                  placeholder="e.g. Stripe"
                  value={addForm.name}
                  onChange={(e) => setAddForm({ ...addForm, name: e.target.value })}
                />
              </div>

              <div className="tc-form-group">
                <label className="tc-form-label">Careers Page URL</label>
                <input
                  type="url"
                  className="tc-form-input"
                  placeholder="e.g. https://boards.greenhouse.io/stripe"
                  value={addForm.careers_url}
                  onChange={(e) => setAddForm({ ...addForm, careers_url: e.target.value })}
                />
              </div>

              <div className="tc-form-group">
                <label className="tc-form-label">Category</label>
                <select
                  className="tc-form-select"
                  value={addForm.category}
                  onChange={(e) => setAddForm({ ...addForm, category: e.target.value })}
                >
                  {CATEGORIES.filter((c) => c !== 'All').map((cat) => (
                    <option key={cat} value={cat}>
                      {CATEGORY_ICONS[cat]} {cat}
                    </option>
                  ))}
                </select>
              </div>

              {addError && (
                <div className="tc-form-error">
                  <AlertCircle size={13} />
                  {addError}
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setAddOpen(false)}>
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={handleAdd}
                disabled={addLoading}
              >
                {addLoading ? 'Adding...' : 'Add Company'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toast && (
        <div className={`tc-toast ${toast.type}`}>
          {toast.type === 'success' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
          {toast.message}
        </div>
      )}
    </div>
  );
}
