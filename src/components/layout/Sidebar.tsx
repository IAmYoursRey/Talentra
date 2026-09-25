'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { UserProfile, UserRole } from '../../types/auth.types';
import {
  LayoutDashboard,
  FolderKanban,
  PlusCircle,
  Radar,
  Compass,
  FileCheck2,
  Inbox,
  Users,
  School,
  LogOut,
  ExternalLink,
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface SidebarProps {
  currentUser: UserProfile;
  onLogout?: () => void;
  className?: string;
}

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentUser, onLogout, className }) => {
  const pathname = usePathname();

  const getNavItems = (role: UserRole): NavItem[] => {
    switch (role) {
      case 'student':
        return [
          { label: 'Overview', href: '/student', icon: LayoutDashboard },
          { label: 'Portofolio Karya', href: '/student/portfolio', icon: FolderKanban },
          { label: 'Tambah Karya', href: '/student/portfolio/new', icon: PlusCircle },
          { label: 'Peta Kompetensi', href: '/student/skills', icon: Radar },
          { label: 'Rekomendasi Karier', href: '/student/career', icon: Compass },
          { label: 'Digital CV & Verifikasi', href: '/student/cv', icon: FileCheck2 },
        ];
      case 'teacher':
        return [
          { label: 'Dashboard Validator', href: '/teacher', icon: LayoutDashboard },
          { label: 'Antrean Validasi', href: '/teacher/reviews', icon: Inbox, badge: '2 Baru' },
        ];
      case 'admin':
        return [
          { label: 'Ekosistem Talenta', href: '/admin', icon: LayoutDashboard },
          { label: 'Manajemen Pengguna', href: '/admin/users', icon: Users },
          { label: 'Manajemen Kelas', href: '/admin/classes', icon: School },
        ];
      default:
        return [];
    }
  };

  const navItems = getNavItems(currentUser.role);

  const roleBadgeConfig: Record<UserRole, { label: string; bg: string; text: string; border: string }> = {
    student: {
      label: 'Siswa Aktif',
      bg: 'bg-brand-50',
      text: 'text-brand-700',
      border: 'border-brand-200',
    },
    teacher: {
      label: 'Guru Validator',
      bg: 'bg-growth-50',
      text: 'text-growth-700',
      border: 'border-growth-200',
    },
    admin: {
      label: 'Admin Sekolah',
      bg: 'bg-intelligence-50',
      text: 'text-intelligence-700',
      border: 'border-intelligence-200',
    },
  };

  const currentBadge = roleBadgeConfig[currentUser.role] || roleBadgeConfig.student;

  return (
    <aside
      className={cn(
        'w-64 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 h-full',
        className
      )}
    >
      <div>
        {/* Brand Logo & Header */}
        <div className="h-16 px-6 border-b border-slate-100 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500 rounded-lg">
            <div className="w-8 h-8 rounded-lg bg-brand-500 text-white flex items-center justify-center font-bold text-base shadow-xs tracking-tighter">
              T
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-slate-900">
                TALENTRA<span className="text-brand-500">.ID</span>
              </span>
              <span className="block text-[10px] text-slate-400 font-medium -mt-1 tracking-wider uppercase">
                Portofolio Digital
              </span>
            </div>
          </Link>
        </div>

        {/* Role Badge & School info */}
        <div className="p-4 mx-3 my-3 rounded-xl bg-slate-50 border border-slate-100">
          <div className="flex items-center justify-between mb-1">
            <span
              className={cn(
                'text-[11px] font-semibold px-2 py-0.5 rounded-full border',
                currentBadge.bg,
                currentBadge.text,
                currentBadge.border
              )}
            >
              {currentBadge.label}
            </span>
            <span className="text-[11px] text-slate-400 font-mono">{currentUser.maskedIdentifier}</span>
          </div>
          <p className="text-xs font-semibold text-slate-800 truncate">{currentUser.schoolName}</p>
          {currentUser.className && (
            <p className="text-[11px] text-slate-500">{currentUser.className}</p>
          )}
        </div>

        {/* Main Navigation */}
        <nav className="px-3 space-y-1" aria-label="Navigasi Utama">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href !== '/student' && item.href !== '/teacher' && item.href !== '/admin' && pathname.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all group focus:outline-none focus:ring-2 focus:ring-brand-500',
                  isActive
                    ? 'bg-brand-500 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={cn(
                      'w-4 h-4 transition-colors',
                      isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-700'
                    )}
                  />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    className={cn(
                      'px-1.5 py-0.5 rounded text-[10px] font-bold',
                      isActive ? 'bg-white/20 text-white' : 'bg-brand-50 text-brand-700 border border-brand-200'
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Profile & Logout */}
      <div className="p-3 border-t border-slate-100 space-y-2">
        <Link
          href="/verify/tlnt_token_v94b8e21"
          target="_blank"
          className="flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-slate-500 hover:text-brand-600 hover:bg-slate-50 transition-colors"
        >
          <span className="flex items-center gap-2">
            <ExternalLink className="w-3.5 h-3.5" />
            <span>Verifikasi Publik QR</span>
          </span>
          <span className="text-[10px] text-slate-400">Demo</span>
        </Link>

        <div className="pt-2 border-t border-slate-100 flex items-center justify-between px-1">
          <div className="min-w-0 pr-2">
            <p className="text-xs font-bold text-slate-900 truncate">{currentUser.name}</p>
            <p className="text-[11px] text-slate-500 truncate">{currentUser.email}</p>
          </div>
          <button
            type="button"
            onClick={onLogout || (() => window.location.href = '/login')}
            aria-label="Keluar dari sesi"
            className="p-1.5 rounded-lg text-slate-400 hover:text-reject-600 hover:bg-reject-50 transition-colors"
            title="Keluar / Ganti Akun"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
