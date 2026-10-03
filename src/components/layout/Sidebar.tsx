'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { UserProfile, UserRole } from '../../types/auth.types';
import { DemoMenuModal } from '../common/DemoMenuModal';
import {
  LayoutDashboard,
  FolderKanban,
  Radar,
  Compass,
  FileCheck2,
  Inbox,
  Users,
  School,
  LogOut,
  Sliders,
  CheckCircle2,
  BarChart3,
  BookOpen,
  Sparkles,
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface SidebarProps {
  currentUser: UserProfile;
  onLogout?: () => void;
  onNavigate?: () => void;
  className?: string;
}

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentUser, onLogout, onNavigate, className }) => {
  const pathname = usePathname();
  const [isDemoOpen, setIsDemoOpen] = useState(false);

  const getNavItems = (role: UserRole): NavItem[] => {
    switch (role) {
      case 'student':
        return [
          { label: 'Overview', href: '/student', icon: LayoutDashboard },
          { label: 'Portfolio', href: '/student/portfolio', icon: FolderKanban },
          { label: 'Skill Map', href: '/student/skills', icon: Radar },
          { label: 'Career Path', href: '/student/career', icon: Compass },
          { label: 'Digital CV', href: '/student/cv', icon: FileCheck2 },
        ];
      case 'teacher':
        return [
          { label: 'Dashboard', href: '/teacher', icon: LayoutDashboard },
          { label: 'Approval Queue', href: '/teacher/reviews', icon: Inbox, badge: '18' },
          { label: 'Kelas Saya', href: '/teacher/classes', icon: School },
          { label: 'Rubrik', href: '/teacher/rubric', icon: BookOpen },
          { label: 'Riwayat', href: '/teacher/history', icon: CheckCircle2 },
        ];
      case 'admin':
        return [
          { label: 'Overview', href: '/admin', icon: LayoutDashboard },
          { label: 'Talent Heatmap', href: '/admin/heatmap', icon: BarChart3 },
          { label: 'Users', href: '/admin/users', icon: Users },
          { label: 'Classes', href: '/admin/classes', icon: School },
          { label: 'Settings', href: '/admin/settings', icon: Sliders },
        ];
      default:
        return [];
    }
  };

  const navItems = getNavItems(currentUser.role);

  const getRoleLabel = (role: UserRole) => {
    switch (role) {
      case 'student':
        return 'STUDENT';
      case 'teacher':
        return 'TEACHER';
      case 'admin':
        return 'SCHOOL ADMIN';
      default:
        return 'USER';
    }
  };

  const getInitials = (name: string) => {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const getSubtitle = () => {
    if (currentUser.role === 'student') {
      return currentUser.className ? `${currentUser.className} • IPA` : 'Kelas XII • IPA';
    }
    if (currentUser.role === 'teacher') {
      return 'Validator • 3 kelas';
    }
    return currentUser.schoolName || 'SMAN 1 Ngoro';
  };

  return (
    <aside
      className={cn(
        'w-[224px] bg-gradient-to-b from-[#2E1065] via-[#4C1D95] to-[#6D28D9] text-white flex flex-col justify-between shrink-0 h-full select-none shadow-xl border-r border-[#4C1D95]/40',
        className
      )}
    >
      <div>
        {/* Brand Logo & Header */}
        <div className="h-20 px-5 flex items-center gap-3">
          <Link
            href="/"
            onClick={() => onNavigate?.()}
            className="flex items-center gap-3 focus:outline-none focus:ring-2 focus:ring-purple-400 rounded-lg group"
          >
            <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-[#6D28D9] via-[#8B5CF6] to-[#A855F7] flex items-center justify-center font-black text-white text-base shadow-md group-hover:scale-105 transition-transform">
              T
              <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-[#C084FC] ring-2 ring-[#2E1065]" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-white block leading-none">
                TALENTRA<span className="text-[#C084FC]">.ID</span>
              </span>
              <span className="block text-[9px] text-[#A78BFA] font-bold tracking-widest uppercase mt-1">
                {getRoleLabel(currentUser.role)}
              </span>
            </div>
          </Link>
        </div>

        {/* Navigation Items */}
        <nav className="px-3 pt-3 space-y-1.5" aria-label="Navigasi Utama">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isExact = pathname === item.href;
            const isChild =
              item.href !== '/student' &&
              item.href !== '/teacher' &&
              item.href !== '/admin' &&
              pathname.startsWith(item.href);

            const isActive = isExact || isChild;

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => onNavigate?.()}
                className={cn(
                  'flex items-center justify-between px-3.5 py-2.5 rounded-xl text-[13px] transition-all group focus:outline-none focus:ring-2 focus:ring-purple-400',
                  isActive
                    ? 'bg-[#4C1D95] text-white font-bold shadow-md shadow-purple-950/20 border border-purple-500/30'
                    : 'text-[#D9CDE5] font-medium hover:text-white hover:bg-white/10'
                )}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      'w-2 h-2 rounded-full transition-colors',
                      isActive ? 'bg-[#C084FC] shadow-sm shadow-[#C084FC]' : 'bg-[#6F607D] group-hover:bg-[#A78BFA]'
                    )}
                  />
                  <span className="tracking-tight">{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    className={cn(
                      'px-2 py-0.5 rounded-full text-[10px] font-bold tracking-tight',
                      isActive
                        ? 'bg-[#C084FC] text-[#2E1065]'
                        : 'bg-purple-900/60 text-[#D8B4FE] border border-purple-700/50'
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

      {/* Demo Explorer Trigger */}
      <div className="px-3 pt-2">
        <button
          type="button"
          onClick={() => setIsDemoOpen(true)}
          className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-purple-500/20 to-indigo-500/20 hover:from-purple-500/30 hover:to-indigo-500/30 border border-purple-400/30 text-[#E9D5FF] transition-all shadow-xs"
        >
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>Jelajah Demo Fitur</span>
          </div>
          <span className="text-[10px] bg-purple-400/20 text-[#C084FC] px-1.5 py-0.5 rounded font-mono">
            SEMUA
          </span>
        </button>
      </div>

      {/* Footer Profile & Logout */}
      <div className="p-3 border-t border-[#4C1D95]/60 bg-[#250d53]/40">
        <div className="flex items-center justify-between p-2 rounded-xl bg-[#4C1D95]/50 border border-purple-500/20">
          <div className="flex items-center gap-2.5 min-w-0 pr-1">
            <div className="w-8 h-8 rounded-full bg-[#4C1D95] border border-purple-400/40 text-[#D9CCE8] font-bold text-xs flex items-center justify-center shrink-0">
              {getInitials(currentUser.name)}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold text-white truncate leading-tight">{currentUser.name}</p>
              <p className="text-[10px] text-[#A78BFA] truncate leading-tight mt-0.5">{getSubtitle()}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onLogout || (() => (window.location.href = '/login'))}
            aria-label="Keluar dari sesi"
            className="p-1.5 rounded-lg text-purple-300 hover:text-rose-300 hover:bg-rose-500/20 transition-colors shrink-0"
            title="Keluar"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Demo Menu Modal */}
      <DemoMenuModal
        isOpen={isDemoOpen}
        onClose={() => setIsDemoOpen(false)}
        currentRole={currentUser.role}
      />
    </aside>
  );
};
