'use client';

import React, { useState, useRef, useEffect } from 'react';
import { UserProfile, UserRole } from '../../types/auth.types';
import { authService } from '../../services/auth.service';
import { ChangePasswordModal } from '../common/ChangePasswordModal';
import {
  Bell,
  Menu,
  Shield,
  LogOut,
  KeyRound,
  User,
  ChevronDown,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ExternalLink,
  Sparkles,
  Loader2,
} from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { cn } from '../../lib/utils';

interface HeaderProps {
  currentUser: UserProfile;
  title?: string;
  onOpenMobileMenu?: () => void;
}

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  time: string;
  type: 'info' | 'success' | 'alert';
}

export const Header: React.FC<HeaderProps> = ({ currentUser, title, onOpenMobileMenu }) => {
  const router = useRouter();
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [isChangePasswordOpen, setIsChangePasswordOpen] = useState(false);
  const [unreadNotif, setUnreadNotif] = useState(true);
  const [switchingRole, setSwitchingRole] = useState<UserRole | null>(null);

  const profileRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setIsProfileOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setIsNotifOpen(false);
      }
    };

    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsProfileOpen(false);
        setIsNotifOpen(false);
      }
    };

    document.addEventListener('mousedown', handleOutsideClick);
    document.addEventListener('keydown', handleEsc);
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleEsc);
    };
  }, []);

  const handleLogout = async () => {
    await authService.logout();
    window.location.href = '/login';
  };

  const handleSwitchDemoRole = async (targetRole: UserRole) => {
    if (switchingRole || targetRole === currentUser.role) return;
    setSwitchingRole(targetRole);
    try {
      const res = await authService.demoLogin(targetRole);
      router.push(res.redirectTo);
    } catch {
      setSwitchingRole(null);
    }
  };

  const getNotifications = (role: UserRole): NotificationItem[] => {
    switch (role) {
      case 'student':
        return [
          {
            id: 'n1',
            title: 'Karya Tervalidasi',
            message: 'Portofolio "Aplikasi Web E-Commerce" telah disetujui oleh Guru Pembimbing.',
            time: '2 jam yang lalu',
            type: 'success',
          },
          {
            id: 'n2',
            title: 'Rekomendasi Karier Baru',
            message: 'Eksplorasi karier Anda telah diperbarui berdasarkan bukti karya tervalidasi.',
            time: '1 hari yang lalu',
            type: 'info',
          },
        ];
      case 'teacher':
        return [
          {
            id: 'n3',
            title: 'Pengajuan Karya Baru',
            message: 'Siswa Demo mengajukan karya baru yang memerlukan asesmen rubrik.',
            time: '10 menit yang lalu',
            type: 'alert',
          },
          {
            id: 'n4',
            title: 'Perbaikan Revisi Diterima',
            message: 'Siswa telah memperbarui catatan pada pengajuan portofolio.',
            time: '3 jam yang lalu',
            type: 'info',
          },
        ];
      case 'admin':
        return [
          {
            id: 'n5',
            title: 'Sinkronisasi Rombel Berhasil',
            message: '36 akun siswa kelas XII RPL 1 aktif untuk tahun ajaran 2025/2026.',
            time: '1 jam yang lalu',
            type: 'success',
          },
          {
            id: 'n6',
            title: 'Audit Keamanan Sistem',
            message: 'Integritas sesi HMAC-SHA256 & verifikasi token berjalan normal.',
            time: 'Kemarin',
            type: 'info',
          },
        ];
      default:
        return [];
    }
  };

  const notifications = getNotifications(currentUser.role);

  return (
    <>
      <header className="h-16 bg-white border-b border-slate-200/80 px-4 sm:px-6 flex items-center justify-between shrink-0 sticky top-9 z-30">
        <div className="flex items-center gap-3">
          {onOpenMobileMenu && (
            <button
              type="button"
              onClick={onOpenMobileMenu}
              aria-label="Buka menu navigasi"
              className="md:hidden p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}
          <div>
            <h1 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
              {title || 'TALENTRA.ID'}
            </h1>
            <p className="text-[11px] text-slate-500 hidden sm:block">
              {currentUser.schoolName}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-2.5">
          {/* Quick Demo Switchers */}
          <div className="hidden sm:flex items-center gap-1 bg-purple-50/80 p-1 rounded-xl border border-purple-100">
            <span className="text-[10px] font-bold text-purple-700 px-1.5 uppercase">Akun Demo:</span>
            <button
              type="button"
              onClick={() => handleSwitchDemoRole('student')}
              disabled={Boolean(switchingRole)}
              title="Masuk Akun Siswa Demo"
              className={cn(
                'px-2 py-0.5 rounded-lg text-[11px] font-bold transition-all inline-flex items-center gap-1 disabled:opacity-50',
                currentUser.role === 'student'
                  ? 'bg-[#6D28D9] text-white shadow-2xs'
                  : 'text-purple-700 hover:bg-purple-100'
              )}
            >
              {switchingRole === 'student' && <Loader2 className="w-3 h-3 animate-spin" />}
              <span>Siswa Demo</span>
            </button>
            <button
              type="button"
              onClick={() => handleSwitchDemoRole('teacher')}
              disabled={Boolean(switchingRole)}
              title="Masuk Akun Guru Demo"
              className={cn(
                'px-2 py-0.5 rounded-lg text-[11px] font-bold transition-all inline-flex items-center gap-1 disabled:opacity-50',
                currentUser.role === 'teacher'
                  ? 'bg-growth-600 text-white shadow-2xs'
                  : 'text-purple-700 hover:bg-purple-100'
              )}
            >
              {switchingRole === 'teacher' && <Loader2 className="w-3 h-3 animate-spin" />}
              <span>Guru Demo</span>
            </button>
            <button
              type="button"
              onClick={() => handleSwitchDemoRole('admin')}
              disabled={Boolean(switchingRole)}
              title="Masuk Akun Admin Demo"
              className={cn(
                'px-2 py-0.5 rounded-lg text-[11px] font-bold transition-all inline-flex items-center gap-1 disabled:opacity-50',
                currentUser.role === 'admin'
                  ? 'bg-intelligence-600 text-white shadow-2xs'
                  : 'text-purple-700 hover:bg-purple-100'
              )}
            >
              {switchingRole === 'admin' && <Loader2 className="w-3 h-3 animate-spin" />}
              <span>Admin Demo</span>
            </button>
          </div>

          {/* Verification Link pill */}
          <Link
            href="/verify/tlnt_token_v94b8e21"
            target="_blank"
            className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition-colors"
          >
            <Shield className="w-3.5 h-3.5" />
            <span>Verifikasi Publik</span>
          </Link>

          {/* Notifications Popover */}
          <div className="relative" ref={notifRef}>
            <button
              type="button"
              aria-label={`Notifikasi (${unreadNotif ? 'Ada baru' : 'Tidak ada baru'})`}
              onClick={() => {
                setIsNotifOpen(!isNotifOpen);
                setUnreadNotif(false);
                setIsProfileOpen(false);
              }}
              className="relative p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <Bell className="w-4 h-4" />
              {unreadNotif && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-brand-500 animate-pulse" />
              )}
            </button>

            {isNotifOpen && (
              <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl shadow-xl border border-slate-200 py-3 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="px-4 pb-2 border-b border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Bell className="w-4 h-4 text-brand-600" />
                    <span className="text-xs font-bold text-slate-900">Pemberitahuan Sistem</span>
                  </div>
                  <span className="text-[10px] font-medium text-slate-400">
                    {notifications.length} Terkini
                  </span>
                </div>

                <div className="divide-y divide-slate-100 max-h-72 overflow-y-auto">
                  {notifications.map((n) => (
                    <div key={n.id} className="p-3.5 hover:bg-slate-50 transition-colors">
                      <div className="flex items-start gap-2.5">
                        <div className="mt-0.5 shrink-0">
                          {n.type === 'success' ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          ) : n.type === 'alert' ? (
                            <AlertTriangle className="w-4 h-4 text-amber-600" />
                          ) : (
                            <Sparkles className="w-4 h-4 text-brand-500" />
                          )}
                        </div>
                        <div className="min-w-0 space-y-0.5">
                          <p className="text-xs font-bold text-slate-900 leading-snug">{n.title}</p>
                          <p className="text-[11px] text-slate-600 leading-relaxed">{n.message}</p>
                          <span className="block text-[10px] text-slate-400 font-mono">{n.time}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="px-4 pt-2 border-t border-slate-100 text-center">
                  <button
                    type="button"
                    onClick={() => setIsNotifOpen(false)}
                    className="text-[11px] font-semibold text-brand-600 hover:text-brand-700"
                  >
                    Tutup Notifikasi
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* User Profile Dropdown */}
          <div className="relative" ref={profileRef}>
            <button
              type="button"
              onClick={() => {
                setIsProfileOpen(!isProfileOpen);
                setIsNotifOpen(false);
              }}
              className="flex items-center gap-2 pl-2 border-l border-slate-200 text-left rounded-lg p-1 hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500"
              aria-expanded={isProfileOpen}
              aria-label="Menu akun pengguna"
            >
              <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-xs uppercase border border-brand-200">
                {currentUser.name.charAt(0)}
              </div>
              <div className="hidden lg:block">
                <p className="text-xs font-bold text-slate-900 leading-tight truncate max-w-[130px]">
                  {currentUser.name}
                </p>
                <p className="text-[10px] text-slate-500 capitalize">{currentUser.role}</p>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {isProfileOpen && (
              <div className="absolute right-0 mt-2 w-72 bg-white rounded-2xl shadow-xl border border-slate-200 py-3 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                {/* User Summary Card */}
                <div className="px-4 pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2.5">
                    <div className="w-10 h-10 rounded-full bg-brand-50 text-brand-700 font-bold text-sm flex items-center justify-center border border-brand-200 shrink-0">
                      {currentUser.name.charAt(0)}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-slate-900 truncate">{currentUser.name}</p>
                      <p className="text-[11px] text-slate-500 truncate">{currentUser.email}</p>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border capitalize">
                          {currentUser.role}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {currentUser.maskedIdentifier}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Account Actions */}
                <div className="py-1">
                  <button
                    type="button"
                    onClick={() => {
                      setIsProfileOpen(false);
                      setIsChangePasswordOpen(true);
                    }}
                    className="w-full px-4 py-2.5 flex items-center gap-2.5 text-xs text-slate-700 hover:bg-slate-50 font-medium transition-colors text-left"
                  >
                    <KeyRound className="w-4 h-4 text-slate-400" />
                    <span>Ganti Kata Sandi</span>
                  </button>

                  <Link
                    href="/verify/tlnt_token_v94b8e21"
                    target="_blank"
                    onClick={() => setIsProfileOpen(false)}
                    className="w-full px-4 py-2.5 flex items-center justify-between text-xs text-slate-700 hover:bg-slate-50 font-medium transition-colors"
                  >
                    <span className="flex items-center gap-2.5">
                      <Shield className="w-4 h-4 text-slate-400" />
                      <span>Verifikasi Publik QR</span>
                    </span>
                    <ExternalLink className="w-3 h-3 text-slate-400" />
                  </Link>
                </div>

                {/* Role Switcher Demo */}
                <div className="px-4 py-2 bg-slate-50/70 border-t border-b border-slate-100 space-y-1.5">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                    Ganti Mode Peran:
                  </span>
                  <div className="grid grid-cols-3 gap-1">
                    {(['student', 'teacher', 'admin'] as UserRole[]).map((r) => (
                      <button
                        key={r}
                        type="button"
                        onClick={() => handleSwitchDemoRole(r)}
                        disabled={Boolean(switchingRole)}
                        className={cn(
                          'py-1 px-1.5 rounded-lg text-[10px] font-semibold border transition-all text-center capitalize inline-flex items-center justify-center gap-1 disabled:opacity-50',
                          currentUser.role === r
                            ? 'bg-brand-500 text-white border-brand-500'
                            : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-100'
                        )}
                      >
                        {switchingRole === r && <Loader2 className="w-2.5 h-2.5 animate-spin" />}
                        <span>{r === 'student' ? 'Siswa' : r === 'teacher' ? 'Guru' : 'Admin'}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Logout Button */}
                <div className="pt-2 px-2">
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="w-full px-3 py-2 rounded-xl text-xs font-semibold text-reject-600 hover:bg-reject-50 flex items-center gap-2 transition-colors text-left"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Keluar dari Sesi</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Change Password Modal */}
      <ChangePasswordModal
        isOpen={isChangePasswordOpen}
        onClose={() => setIsChangePasswordOpen(false)}
      />
    </>
  );
};
