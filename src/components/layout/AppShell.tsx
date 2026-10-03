'use client';

import React, { useState, useEffect } from 'react';
import { UserRole, UserProfile } from '../../types/auth.types';
import { authService } from '../../services/auth.service';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { MobileNav } from './MobileNav';
import { DemoAccessBanner } from './DemoAccessBanner';
import { ForbiddenState } from '../common/ForbiddenState';
import { LoadingSkeleton } from '../common/LoadingSkeleton';
import { X } from 'lucide-react';

interface AppShellProps {
  children: React.ReactNode;
  pageTitle?: string;
  expectedRole?: UserRole;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  pageTitle,
  expectedRole,
}) => {
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);

  useEffect(() => {
    authService.getCurrentSession().then((session) => {
      setCurrentUser(session.user);
      setIsLoading(false);
    });

    const unsubscribe = authService.subscribeSession(() => {
      authService.getCurrentSession().then((session) => {
        setCurrentUser(session.user);
      });
    });

    return unsubscribe;
  }, []);

  if (isLoading || !currentUser) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
        <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-xs border border-slate-200">
          <LoadingSkeleton rows={4} />
        </div>
      </div>
    );
  }

  const handleLogout = async () => {
    await authService.logout();
    window.location.href = '/login';
  };

  const isForbidden = expectedRole && currentUser.role !== expectedRole;

  return (
    <div className="min-h-screen bg-[#FCFBFF] flex flex-col font-sans text-[#261331] antialiased selection:bg-[#6D28D9] selection:text-white">
      {/* Top Demo Access Banner */}
      <DemoAccessBanner />

      <div className="flex-1 flex overflow-hidden">
        {/* Desktop Sidebar */}
        <Sidebar
          currentUser={currentUser}
          onLogout={handleLogout}
          className="hidden md:flex"
        />

        {/* Mobile Drawer Backdrop & Sidebar */}
        {isMobileDrawerOpen && (
          <div
            className="md:hidden fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex animate-in fade-in duration-200"
            onClick={() => setIsMobileDrawerOpen(false)}
          >
            <div
              className="w-72 bg-gradient-to-b from-[#2E1065] via-[#4C1D95] to-[#6D28D9] h-full shadow-2xl relative flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="absolute top-4 right-4 z-10">
                <button
                  type="button"
                  onClick={() => setIsMobileDrawerOpen(false)}
                  className="p-1 rounded-lg text-white/70 hover:text-white bg-white/10"
                  aria-label="Tutup menu navigasi"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <Sidebar
                currentUser={currentUser}
                onLogout={handleLogout}
                onNavigate={() => setIsMobileDrawerOpen(false)}
                className="w-full h-full border-r-0"
              />
            </div>
          </div>
        )}

        {/* Content Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          <Header
            currentUser={currentUser}
            title={pageTitle}
            onOpenMobileMenu={() => setIsMobileDrawerOpen(true)}
          />

          <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto pb-20 md:pb-8">
            {isForbidden ? (
              <ForbiddenState
                requiredRole={expectedRole}
                currentRole={currentUser.role}
                onSwitchRole={async () => {
                  try {
                    const res = await authService.demoLogin(expectedRole!);
                    window.location.href = res.redirectTo;
                  } catch {
                    // Fallback
                  }
                }}
              />
            ) : (
              children
            )}
          </main>
        </div>
      </div>

      {/* Mobile Bottom Navigation */}
      <MobileNav role={currentUser.role} />
    </div>
  );
};
