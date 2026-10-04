'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { useSidebar } from '@/lib/sidebar-context';
import { Search, LogOut, Menu, Layers, BookOpen } from 'lucide-react';

export function Topbar() {
  const { user, loading, logout, openAuthModal, loginAsDemo } = useAuth();
  const { toggle: toggleSidebar } = useSidebar();

  return (
    <header className="topbar">
      {/* Left: Mobile Menu Toggle + Logo */}
      <div className="topbar-left">
        <button
          type="button"
          className="topbar-menu-btn"
          onClick={toggleSidebar}
          aria-label="Toggle navigation menu"
        >
          <Menu size={18} />
        </button>

        <Link href="/" className="topbar-logo">
          <div className="topbar-logo-icon">
            <Layers size={15} />
          </div>
          <span className="topbar-brand-name">JobForge</span>
          <span className="topbar-badge">COMMAND CENTER</span>
        </Link>
      </div>

      {/* Center: Search Trigger */}
      <button
        type="button"
        className="topbar-search-trigger"
        onClick={() => (window.location.href = '/jobs')}
        aria-label="Search jobs, companies, skills"
      >
        <Search size={14} className="topbar-search-icon" />
        <span className="topbar-search-text">Search jobs, companies, skills...</span>
        <kbd className="topbar-kbd">⌘K</kbd>
      </button>

      {/* How It Works Guide Link */}
      <Link href="/landing" className="topbar-guide-link" title="Platform Guide & Walkthrough">
        <BookOpen size={13} style={{ color: 'var(--accent)' }} />
        <span>How It Works</span>
      </Link>

      {/* Right Controls */}
      <div className="topbar-right">
        {loading ? (
          <span className="topbar-loading-text">Loading...</span>
        ) : user ? (
          <div className="topbar-user-area">
            <div className="topbar-user-info">
              <div className="avatar-badge">
                {(user.name || user.email || 'U')[0].toUpperCase()}
              </div>
              <span className="topbar-user-name">
                {user.name || user.email?.split('@')[0]}
              </span>
            </div>

            <button
              onClick={logout}
              className="btn btn-ghost btn-sm"
              title="Sign Out"
            >
              <LogOut size={13} />
              <span className="topbar-hide-mobile">Sign out</span>
            </button>
          </div>
        ) : (
          <div className="topbar-auth-buttons">
            <button
              onClick={() => loginAsDemo().then(() => window.location.reload())}
              className="btn btn-secondary btn-sm"
            >
              Demo Mode
            </button>
            <button
              onClick={() => openAuthModal('login')}
              className="btn btn-primary btn-sm"
            >
              Sign In
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
