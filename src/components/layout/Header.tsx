'use client';

import React from 'react';
import { UserProfile } from '../../types/auth.types';
import { Bell, Menu, Shield } from 'lucide-react';
import Link from 'next/link';

interface HeaderProps {
  currentUser: UserProfile;
  title?: string;
  onOpenMobileMenu?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ currentUser, title, onOpenMobileMenu }) => {
  return (
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

      <div className="flex items-center gap-2.5">
        {/* Verification Link pill */}
        <Link
          href="/verify/tlnt_token_v94b8e21"
          target="_blank"
          className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition-colors"
        >
          <Shield className="w-3.5 h-3.5" />
          <span>Verifikasi Publik</span>
        </Link>

        {/* Notifications placeholder */}
        <button
          type="button"
          aria-label="Notifikasi (2 baru)"
          onClick={() => alert('Pusat Notifikasi TALENTRA: Belum ada notifikasi mendesak baru.')}
          className="relative p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-brand-500" />
        </button>

        {/* User Mini Profile */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-xs uppercase border border-brand-200">
            {currentUser.name.charAt(0)}
          </div>
          <div className="hidden lg:block text-left">
            <p className="text-xs font-bold text-slate-900 leading-tight">{currentUser.name}</p>
            <p className="text-[10px] text-slate-500 capitalize">{currentUser.role}</p>
          </div>
        </div>
      </div>
    </header>
  );
};
