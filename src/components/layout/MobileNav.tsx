'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { UserRole } from '../../types/auth.types';
import {
  LayoutDashboard,
  FolderKanban,
  PlusCircle,
  Radar,
  FileCheck2,
  Inbox,
  Users,
  School,
  Compass,
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface MobileNavProps {
  role: UserRole;
  className?: string;
}

export const MobileNav: React.FC<MobileNavProps> = ({ role, className }) => {
  const pathname = usePathname();

  const getItems = (currentRole: UserRole) => {
    switch (currentRole) {
      case 'student':
        return [
          { label: 'Beranda', href: '/student', icon: LayoutDashboard },
          { label: 'Karya', href: '/student/portfolio', icon: FolderKanban },
          { label: '+ Buat', href: '/student/portfolio/new', icon: PlusCircle, highlight: true },
          { label: 'Kompetensi', href: '/student/skills', icon: Radar },
          { label: 'CV', href: '/student/cv', icon: FileCheck2 },
        ];
      case 'teacher':
        return [
          { label: 'Overview', href: '/teacher', icon: LayoutDashboard },
          { label: 'Antrean Validasi', href: '/teacher/reviews', icon: Inbox },
        ];
      case 'admin':
        return [
          { label: 'Ringkasan', href: '/admin', icon: LayoutDashboard },
          { label: 'Pengguna', href: '/admin/users', icon: Users },
          { label: 'Kelas', href: '/admin/classes', icon: School },
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
        'md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-slate-200 px-2 py-1 shadow-lg',
        className
      )}
    >
      <div className="flex items-center justify-around max-w-md mx-auto">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          if (item.highlight) {
            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex flex-col items-center justify-center -mt-4 group"
              >
                <div className="w-11 h-11 rounded-full bg-brand-500 text-white flex items-center justify-center shadow-md group-active:scale-95 transition-transform">
                  <Icon className="w-5 h-5" />
                </div>
                <span className="text-[10px] font-bold text-brand-600 mt-0.5">{item.label}</span>
              </Link>
            );
          }

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex flex-col items-center justify-center py-1 px-2 rounded-lg transition-colors min-w-[56px]',
                isActive ? 'text-brand-600 font-semibold' : 'text-slate-500 hover:text-slate-800'
              )}
            >
              <Icon className={cn('w-4 h-4', isActive ? 'text-brand-600' : 'text-slate-400')} />
              <span className="text-[10px] mt-0.5">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};
