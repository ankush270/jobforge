'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { auth, type User } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  token: string | null;
  isAuthModalOpen: boolean;
  openAuthModal: (mode?: 'login' | 'register') => void;
  closeAuthModal: () => void;
  authMode: 'login' | 'register';
  setAuthMode: (mode: 'login' | 'register') => void;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  loginAsDemo: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  const fetchUser = useCallback(async () => {
    const savedToken = typeof window !== 'undefined' ? localStorage.getItem('jobforge_token') : null;
    if (!savedToken) {
      setUser(null);
      setToken(null);
      setLoading(false);
      return;
    }

    try {
      const u = await auth.me();
      setUser(u);
      setToken(savedToken);
    } catch {
      localStorage.removeItem('jobforge_token');
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const openAuthModal = (mode: 'login' | 'register' = 'login') => {
    setAuthMode(mode);
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
  };

  const login = async (email: string, password: string) => {
    const res = await auth.login({ email, password });
    localStorage.setItem('jobforge_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    setIsAuthModalOpen(false);
  };

  const register = async (name: string, email: string, password: string) => {
    const res = await auth.register({ name, email, password });
    localStorage.setItem('jobforge_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    setIsAuthModalOpen(false);
  };

  const loginAsDemo = async () => {
    try {
      await login('demo@jobforge.ai', 'demo12345');
    } catch {
      // If user doesn't exist yet, register demo user
      try {
        await register('Demo User', 'demo@jobforge.ai', 'demo12345');
      } catch (err: unknown) {
        const error = err as Error;
        throw new Error(error.message || 'Failed to login with demo account');
      }
    }
  };

  const logout = () => {
    localStorage.removeItem('jobforge_token');
    setUser(null);
    setToken(null);
    window.location.reload();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        token,
        isAuthModalOpen,
        openAuthModal,
        closeAuthModal,
        authMode,
        setAuthMode,
        login,
        register,
        logout,
        loginAsDemo,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
