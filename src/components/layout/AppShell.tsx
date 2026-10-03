'use client';

import React, { useState, useEffect } from 'react';
import { UserRole, UserProfile } from '../../types/auth.types';
import { authService } from '../../services/auth.service';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { MobileNav } from './MobileNav';
import { DemoAccessBanner } from './DemoAccessBanner';
import { ForbiddenState } from '../common/ForbiddenState';
import { X, WifiOff } from 'lucide-react';
import { useOffline } from '../../context/OfflineContext';

interface AppShellProps {
  children: React.ReactNode;
  pageTitle?: string;
  expectedRole?: UserRole;
  isPageLoading?: boolean;
  loadingMessage?: string;
  loadingSubMessage?: string;
}

const getFallbackUser = (expectedRole?: UserRole): UserProfile => {
  if (expectedRole === 'teacher') {
    return {
      id: 'teacher-demo',
      name: 'Guru Demo',
      role: 'teacher',
      email: 'guru.demo@sekolah.sch.id',
      schoolName: 'SMKN 1 Jakarta',
      maskedIdentifier: 'NUPTK 1985***',
      title: 'Pembimbing Portofolio & Kejuruan',
    };
  }
  if (expectedRole === 'admin') {
    return {
      id: 'admin-demo',
      name: 'Admin Demo',
      role: 'admin',
      email: 'admin.demo@sekolah.sch.id',
      schoolName: 'SMKN 1 Jakarta',
      maskedIdentifier: 'NPSN 2010***',
      title: 'Administrator Sekolah & IT',
    };
  }
  return {
    id: 'student-demo',
    name: 'Dimas Pratama',
    role: 'student',
    email: 'dimas.pratama@siswa.sch.id',
    schoolName: 'SMKN 1 Jakarta',
    maskedIdentifier: 'NISN 008***',
    grade: 'XII',
    className: 'XII RPL 1',
  };
};

export const AppShell: React.FC<AppShellProps> = ({
  children,
  pageTitle,
  expectedRole,
  isPageLoading = false,
  loadingMessage,
  loadingSubMessage,
}) => {
  const [currentUser, setCurrentUser] = useState<UserProfile>(() => getFallbackUser(expectedRole));
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState(false);
  const { isOffline } = useOffline();

  useEffect(() => {
    let active = true;

    if (typeof window !== 'undefined') {
      const cached = authService.getCurrentUser();
      if (cached && active) {
        setCurrentUser(cached);
      }

      authService.getCurrentSession().then((session) => {
        if (active && session.user) {
          setCurrentUser(session.user);
        }
      });

      const unsubscribe = authService.subscribeSession(() => {
        authService.getCurrentSession().then((session) => {
          if (active && session.user) {
            setCurrentUser(session.user);
          }
        });
      });

      return () => {
        active = false;
        unsubscribe();
      };
    }
  }, []);

  const handleLogout = async () => {
    await authService.logout();
    window.location.href = '/login';
  };

  const isForbidden = expectedRole && currentUser.role !== expectedRole;

  return (
    <div className="h-screen max-h-screen w-screen bg-[#FCFBFF] flex flex-col font-sans text-[#261331] antialiased overflow-hidden selection:bg-[#6D28D9] selection:text-white">
      {/* Top Demo Access Banner */}
      <DemoAccessBanner />

      {/* Offline Status Notification */}
      {isOffline && (
        <aside
          role="status"
          className="bg-gradient-to-r from-amber-600 via-amber-500 to-amber-600 text-white text-xs font-semibold px-4 py-2 flex items-center justify-between shadow-xs sticky top-0 z-40 backdrop-blur-md animate-in fade-in"
        >
          <div className="flex items-center gap-2 max-w-7xl mx-auto w-full justify-between">
            <div className="flex items-center gap-2">
              <WifiOff className="w-4 h-4 text-amber-200 shrink-0 animate-pulse" />
              <span>
                <strong>Mode Offline (Luring):</strong> Menampilkan data tersimpan. Seluruh halaman tetap dapat Anda tinjau; aksi perubahan data dinonaktifkan sementara hingga terhubung kembali.
              </span>
            </div>
            <span className="text-[10px] uppercase font-black bg-amber-900/30 px-2 py-0.5 rounded-full border border-amber-300/40 shrink-0">
              Tersimpan Lokal
            </span>
          </div>
        </aside>
      )}

      {/* Local Page Loading Progress Bar (Non-blocking) */}
      {isPageLoading && (
        <div className="w-full h-1 bg-purple-100 overflow-hidden relative shrink-0 z-30">
          <div className="absolute top-0 bottom-0 left-0 w-2/3 bg-gradient-to-r from-[#6D28D9] to-[#C084FC] rounded-full animate-indeterminate" />
        </div>
      )}

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
