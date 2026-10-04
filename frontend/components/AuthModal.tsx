'use client';

import React, { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { X } from 'lucide-react';

export function AuthModal() {
  const { isAuthModalOpen, closeAuthModal, authMode, setAuthMode, login, register, loginAsDemo } =
    useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (authMode === 'login') {
        await login(email, password);
      } else {
        await register(name, email, password);
      }
      window.location.reload();
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || 'Authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = async () => {
    setError(null);
    setLoading(true);
    try {
      await loginAsDemo();
      window.location.reload();
    } catch (err: unknown) {
      const e = err as Error;
      setError(e.message || 'Demo login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={closeAuthModal}>
      <div
        className="modal-dialog"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '400px' }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
          }}
        >
          <h2 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#fff' }}>
            {authMode === 'login' ? 'Sign In' : 'Create Account'}
          </h2>
          <button
            onClick={closeAuthModal}
            className="btn btn-ghost btn-sm"
          >
            <X size={15} />
          </button>
        </div>

        {/* Tab switch */}
        <div
          style={{
            display: 'flex',
            gap: '4px',
            marginBottom: '16px',
            background: '#16161a',
            padding: '3px',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          <button
            type="button"
            className={`btn btn-sm ${authMode === 'login' ? 'btn-secondary' : 'btn-ghost'}`}
            style={{ flex: 1 }}
            onClick={() => {
              setAuthMode('login');
              setError(null);
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`btn btn-sm ${authMode === 'register' ? 'btn-secondary' : 'btn-ghost'}`}
            style={{ flex: 1 }}
            onClick={() => {
              setAuthMode('register');
              setError(null);
            }}
          >
            Register
          </button>
        </div>

        {/* Quick Demo Button */}
        <div style={{ marginBottom: '16px' }}>
          <button
            type="button"
            onClick={handleQuickDemo}
            disabled={loading}
            className="btn btn-secondary"
            style={{ width: '100%', padding: '8px' }}
          >
            Demo Login
          </button>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              margin: '14px 0 6px',
              color: 'var(--text-dim)',
              fontSize: '0.72rem',
            }}
          >
            <div style={{ flex: 1, height: '1px', background: 'var(--border-subtle)' }} />
            <span>OR</span>
            <div style={{ flex: 1, height: '1px', background: 'var(--border-subtle)' }} />
          </div>
        </div>

        {error && (
          <div
            style={{
              padding: '8px 12px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(244, 63, 94, 0.1)',
              border: '1px solid rgba(244, 63, 94, 0.25)',
              color: '#fb7185',
              fontSize: '0.82rem',
              marginBottom: '14px',
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {authMode === 'register' && (
            <div>
              <label className="label">Name</label>
              <input
                type="text"
                className="input"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
          )}

          <div>
            <label className="label">Email</label>
            <input
              type="email"
              className="input"
              placeholder="you@domain.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="label">Password</label>
            <input
              type="password"
              className="input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
            style={{ marginTop: '4px', width: '100%' }}
          >
            {loading ? 'Authenticating...' : authMode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  );
}
