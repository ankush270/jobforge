'use client';

import React from 'react';
import { AuthProvider } from '@/lib/auth-context';
import { SidebarProvider } from '@/lib/sidebar-context';
import { AuthModal } from '@/components/AuthModal';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <SidebarProvider>
        {children}
        <AuthModal />
      </SidebarProvider>
    </AuthProvider>
  );
}

