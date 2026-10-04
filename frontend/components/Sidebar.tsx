'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  Kanban,
  BarChart3,
  Mail,
  Mic,
  DollarSign,
  HelpCircle,
  Users,
  X,
  Layers,
  Zap,
  Activity,
  LogOut,
  ChevronRight,
  ShieldCheck,
  BookOpen,
  Code2,
  Cpu,
  Building2,
} from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import { useSidebar } from '@/lib/sidebar-context';

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { isOpen, close } = useSidebar();

  const navItems = [
    {
      href: '/',
      label: 'Command Center',
      icon: LayoutDashboard,
    },
    {
      href: '/landing',
      label: 'Platform Guide',
      icon: BookOpen,
      badge: { text: 'Guide', type: 'accent' },
    },
    {
      href: '/jobs',
      label: 'Parsed Jobs Feed',
      icon: Briefcase,
      badge: { text: 'LIVE', type: 'live' },
    },
    {
      href: '/resumes',
      label: 'Master Resumes',
      icon: FileText,
      badge: { text: 'ATS', type: 'neutral' },
    },
    {
      href: '/applications',
      label: 'Kanban Tracker',
      icon: Kanban,
      badge: { text: 'Stages', type: 'neutral' },
    },
    {
      href: '/analytics',
      label: 'Pipeline Analytics',
      icon: BarChart3,
    },
    {
      href: '/companies',
      label: 'Company Directory',
      icon: Building2,
      badge: { text: '290+', type: 'accent' },
    },
  ];

  const toolItems = [
    {
      href: '/tailor',
      label: 'Resume STAR Tailor',
      icon: Code2,
      badge: { text: 'ATS', type: 'accent' },
    },
    {
      href: '/cover-letter',
      label: 'Cover Letter Builder',
      icon: Mail,
      badge: { text: 'Direct', type: 'neutral' },
    },
    {
      href: '/interview-prep',
      label: 'Interview STAR Bank',
      icon: Mic,
      badge: { text: 'PRO', type: 'pro' },
    },
    {
      href: '/salary',
      label: 'Salary Benchmarks',
      icon: DollarSign,
    },
    {
      href: '/qa-bank',
      label: 'QA Intelligence',
      icon: HelpCircle,
    },
    {
      href: '/contacts',
      label: 'Recruiter Outreach',
      icon: Users,
    },
  ];

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      <div
        className={`sidebar-overlay ${isOpen ? 'open' : ''}`}
        onClick={close}
        aria-hidden="true"
      />

      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        {/* Mobile Header (Only visible on small screens) */}
        <div className="sidebar-mobile-header">
          <div className="sidebar-mobile-brand">
            <div className="topbar-logo-icon">
              <Layers size={14} />
            </div>
            <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
              JobForge
            </span>
          </div>
          <button
            type="button"
            className="sidebar-close-btn"
            onClick={close}
            aria-label="Close navigation"
          >
            <X size={16} />
          </button>
        </div>

        {/* Top Mini Workspace Pill */}
        <div className="sidebar-header-card">
          <div className="sidebar-header-row">
            <div className="sidebar-target-icon">
              <Zap size={13} />
            </div>
            <div className="sidebar-target-text">
              <span className="sidebar-target-title">AI Application Engine</span>
              <span className="sidebar-target-subtitle">Real-time matching &middot; v2.4</span>
            </div>
          </div>
        </div>

        {/* Section: Core Pipeline */}
        <div className="sidebar-section-header">
          <span className="sidebar-section-title">Core Pipeline</span>
          <span className="sidebar-section-count">6 Modules</span>
        </div>
        <ul className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                  onClick={close}
                >
                  {isActive && <span className="sidebar-active-indicator" />}
                  <span className="sidebar-nav-icon-wrap">
                    <Icon size={15} strokeWidth={isActive ? 2.2 : 1.7} />
                  </span>
                  <span className="sidebar-nav-text">{item.label}</span>
                  {item.badge && (
                    <span className={`sidebar-pill-badge ${item.badge.type}`}>
                      {item.badge.type === 'live' && <span className="sidebar-pulse-dot" />}
                      {item.badge.text}
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>

        {/* Section: AI Copilots */}
        <div className="sidebar-section-header" style={{ marginTop: '22px' }}>
          <span className="sidebar-section-title">AI Copilots &amp; Tools</span>
          <span className="sidebar-section-count">6 Tools</span>
        </div>
        <ul className="sidebar-nav">
          {toolItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                  onClick={close}
                >
                  {isActive && <span className="sidebar-active-indicator" />}
                  <span className="sidebar-nav-icon-wrap">
                    <Icon size={15} strokeWidth={isActive ? 2.2 : 1.7} />
                  </span>
                  <span className="sidebar-nav-text">{item.label}</span>
                  {item.badge && (
                    <span className={`sidebar-pill-badge ${item.badge.type}`}>
                      {item.badge.text}
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>

        {/* Direct ATS Engine Mini-Widget */}
        <div className="sidebar-mini-widget">
          <div className="sidebar-widget-header">
            <div className="sidebar-widget-badge">
              <Cpu size={11} />
              <span>ATS Engine</span>
            </div>
            <span className="sidebar-widget-score">94% Fit</span>
          </div>
          <p className="sidebar-widget-desc">Anti-hallucination Star bullet generator active</p>
          <div className="sidebar-widget-progress-bg">
            <div className="sidebar-widget-progress-fill" style={{ width: '94%' }} />
          </div>
        </div>

        {/* System Status & Footer */}
        <div className="sidebar-footer">
          <div className="sidebar-status-container">
            <span className="status-dot" />
            <span className="status-label">All Systems Live</span>
            <span className="sidebar-status-latency">24ms</span>
          </div>

          {user ? (
            <div className="sidebar-user-card">
              <div className="avatar-badge">
                {(user.name || user.email || 'U')[0].toUpperCase()}
              </div>
              <div className="sidebar-user-details">
                <span className="sidebar-user-name">
                  {user.name || user.email?.split('@')[0]}
                </span>
                <span className="sidebar-user-role">Applicant Pro Tier</span>
              </div>
              <button
                type="button"
                onClick={logout}
                className="sidebar-user-logout-btn"
                title="Sign Out"
                aria-label="Sign Out"
              >
                <LogOut size={13} />
              </button>
            </div>
          ) : (
            <div className="sidebar-guest-card">
              <div className="sidebar-guest-icon">
                <ShieldCheck size={14} />
              </div>
              <div className="sidebar-guest-details">
                <span className="sidebar-guest-title">Demo Session</span>
                <span className="sidebar-guest-desc">Full access enabled</span>
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
