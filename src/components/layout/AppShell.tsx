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
import { CircularLogoSpinner } from '../common/CircularLogoSpinner';
import { X } from 'lucide-react';

interface AppShellProps {
  children: React.ReactNode;
  pageTitle?: string;
  expectedRole?: UserRole;
  isPageLoading?: boolean;
  loadingMessage?: string;
  loadingSubMessage?: string;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  pageTitle,
  expectedRole,
  isPageLoading = false,
  loadingMessage,
  loadingSubMessage,
}) => {
  const [isMounted, setIsMounted] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    let active = true;

    const cached = authService.getCurrentUser();
    if (cached) {
      setCurrentUser(cached);
      setIsLoading(false);
    }

    authService.getCurrentSession().then((session) => {
      if (active) {
        if (session.user) {
          setCurrentUser(session.user);
        }
        setIsLoading(false);
      }
    });

    // Safety timeout: never block navigation for more than 400ms
    const timer = setTimeout(() => {
      if (active) {
        setIsLoading(false);
      }
    }, 400);

    const unsubscribe = authService.subscribeSession(() => {
      authService.getCurrentSession().then((session) => {
        if (active && session.user) {
          setCurrentUser(session.user);
        }
      });
    });

    return () => {
      active = false;
      clearTimeout(timer);
      unsubscribe();
    };
  }, []);

  if (!isMounted || isLoading || !currentUser) {
    return (
      <div
        role="status"
        aria-label="Memuat sesi aplikasi..."
        className="min-h-screen bg-[#FCFBFF] flex flex-col items-center justify-center p-6 select-none animate-in fade-in duration-150"
      >
        <div className="relative flex flex-col items-center max-w-sm text-center space-y-5">
          <CircularLogoSpinner size="lg" />
          <div className="space-y-1.5">
            <h2 className="text-base font-extrabold text-[#261331] tracking-tight">
              Memuat Sesi...
            </h2>
            <p className="text-xs text-[#6F607D]">
              Menyiapkan data portofolio, analitik, dan hak akses.
            </p>
          </div>
          <div className="w-48 h-1.5 bg-purple-100 rounded-full overflow-hidden relative">
            <div className="absolute top-0 bottom-0 left-0 w-2/3 bg-gradient-to-r from-[#6D28D9] to-[#C084FC] rounded-full animate-indeterminate" />
          </div>
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
    <div className="h-screen max-h-screen w-screen bg-[#FCFBFF] flex flex-col font-sans text-[#261331] antialiased overflow-hidden selection:bg-[#6D28D9] selection:text-white">
      {/* Top Demo Access Banner */}
      <DemoAccessBanner />

      <div className="flex-1 flex min-h-0 overflow-hidden relative">
        {/* Desktop Sidebar */}
        <Sidebar
          currentUser={currentUser}
          onLogout={handleLogout}
          className="hidden md:flex h-full"
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

          <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto pb-20 md:pb-8 relative">
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
