'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { UserRole } from '../../types/auth.types';
import {
  LayoutDashboard,
  FolderKanban,
  Radar,
  FileCheck2,
  Inbox,
  Users,
  School,
  Compass,
  Sliders,
  BarChart3,
  BookOpen,
  CheckCircle2,
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface MobileNavProps {
  role: UserRole;
  className?: string;
}

interface MobileNavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

export const MobileNav: React.FC<MobileNavProps> = ({ role, className }) => {
  const pathname = usePathname();

  const getItems = (currentRole: UserRole): MobileNavItem[] => {
    switch (currentRole) {
      case 'student':
        return [
          { label: 'Home', href: '/student', icon: LayoutDashboard },
          { label: 'Portfolio', href: '/student/portfolio', icon: FolderKanban },
          { label: 'Skill', href: '/student/skills', icon: Radar },
          { label: 'Career', href: '/student/career', icon: Compass },
          { label: 'CV', href: '/student/cv', icon: FileCheck2 },
        ];
      case 'teacher':
        return [
          { label: 'Dashboard', href: '/teacher', icon: LayoutDashboard },
          { label: 'Queue', href: '/teacher/reviews', icon: Inbox },
          { label: 'Kelas', href: '/teacher/classes', icon: School },
          { label: 'Rubrik', href: '/teacher/rubric', icon: BookOpen },
          { label: 'Riwayat', href: '/teacher/history', icon: CheckCircle2 },
        ];
      case 'admin':
        return [
          { label: 'Overview', href: '/admin', icon: LayoutDashboard },
          { label: 'Heatmap', href: '/admin/heatmap', icon: BarChart3 },
          { label: 'Users', href: '/admin/users', icon: Users },
          { label: 'Classes', href: '/admin/classes', icon: School },
          { label: 'Settings', href: '/admin/settings', icon: Sliders },
        ];
      default:
        return [];
    }
  };

  const items = getItems(role);

  return (
    <nav
      aria-label="Navigasi bawah perangkat seluler"
      className={cn(
        'md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-[#E9E1F4] px-2 py-1.5 shadow-[0_-4px_16px_rgba(76,29,149,0.06)]',
        className
      )}
    >
      <div className="flex items-center justify-around max-w-md mx-auto">
        {items.map((item) => {
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
              className={cn(
                'flex flex-col items-center justify-center py-1 px-2 rounded-xl transition-all min-w-[50px]',
                isActive
                  ? 'text-[#6D28D9] font-bold'
                  : 'text-[#6F607D] hover:text-[#261331]'
              )}
            >
              <div
                className={cn(
                  'w-8 h-8 rounded-lg flex items-center justify-center transition-all',
                  isActive ? 'bg-[#F7F2FF] text-[#6D28D9] shadow-xs' : 'text-[#9584A7]'
                )}
              >
                <Icon className="w-4 h-4" />
              </div>
              <span className="text-[10px] mt-0.5 tracking-tight truncate max-w-[56px] text-center">
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};
