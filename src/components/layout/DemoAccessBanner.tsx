'use client';

import React, { useState, useEffect } from 'react';
import { authService } from '../../services/auth.service';
import { UserRole, UserProfile } from '../../types/auth.types';
import { useRouter } from 'next/navigation';
import { Sparkles, User, GraduationCap, ShieldCheck, Check, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

export const DemoAccessBanner: React.FC = () => {
  const router = useRouter();
  const [currentRole, setCurrentRole] = useState<UserRole>('student');
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);

  // Enabled by default unless explicitly disabled
  const isDemoAllowed = process.env.NEXT_PUBLIC_ENABLE_DEMO_AUTH !== 'false';

  useEffect(() => {
    if (!isDemoAllowed) return;

    authService.getCurrentSession().then((s) => {
      setCurrentRole(s.role);
      setCurrentUser(s.user);
    });

    const unsubscribe = authService.subscribeSession(() => {
      authService.getCurrentSession().then((s) => {
        setCurrentRole(s.role);
        setCurrentUser(s.user);
      });
    });

    return unsubscribe;
  }, [isDemoAllowed]);

  const [switchingRole, setSwitchingRole] = useState<UserRole | null>(null);

  if (!isDemoAllowed) {
    return null;
  }

  const handleRoleSwitch = async (role: UserRole) => {
    if (switchingRole || role === currentRole) return;
    setSwitchingRole(role);
    try {
      const res = await authService.demoLogin(role);
      router.push(res.redirectTo);
    } catch {
      setSwitchingRole(null);
    }
  };

  return (
    <aside
      aria-label="Mode demonstrasi pengembang"
      className="bg-slate-900 text-slate-100 text-xs py-2 px-3 sm:px-6 flex flex-wrap items-center justify-between gap-2.5 border-b border-slate-800 shadow-xs z-40 sticky top-0 shrink-0"
    >
      <div className="flex items-center gap-2">
        <span className="flex items-center gap-1 font-semibold text-brand-400 bg-brand-950/80 px-2.5 py-0.5 rounded-full border border-brand-800/60">
          <Sparkles className="w-3 h-3 text-amber-300" />
          <span className="tracking-wide">AKUN DEMO AKTIF:</span>
        </span>
        <span className="text-slate-300">
          <strong className="text-white">{currentUser?.name || 'Siswa Demo'}</strong> ({currentUser?.maskedIdentifier || 'NISN 008***'})
        </span>
      </div>

      <div className="flex items-center gap-1.5 flex-wrap">
        <span className="text-slate-400 text-[11px] mr-1 hidden xs:inline">Ganti Akun Demo:</span>
        
        <button
          type="button"
          onClick={() => handleRoleSwitch('student')}
          disabled={Boolean(switchingRole)}
          className={cn(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer disabled:opacity-50',
            currentRole === 'student'
              ? 'bg-brand-500 text-white shadow-2xs font-bold'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
          )}
        >
          {switchingRole === 'student' ? (
            <Loader2 className="w-3 h-3 animate-spin text-white" />
          ) : (
            <User className="w-3 h-3" />
          )}
          <span>{switchingRole === 'student' ? 'Memuat...' : 'Siswa Demo'}</span>
          {currentRole === 'student' && !switchingRole && <Check className="w-3 h-3 ml-0.5" />}
        </button>

        <button
          type="button"
          onClick={() => handleRoleSwitch('teacher')}
          disabled={Boolean(switchingRole)}
          className={cn(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer disabled:opacity-50',
            currentRole === 'teacher'
              ? 'bg-growth-600 text-white shadow-2xs font-bold'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
          )}
        >
          {switchingRole === 'teacher' ? (
            <Loader2 className="w-3 h-3 animate-spin text-white" />
          ) : (
            <GraduationCap className="w-3 h-3" />
          )}
          <span>{switchingRole === 'teacher' ? 'Memuat...' : 'Guru Demo'}</span>
          {currentRole === 'teacher' && !switchingRole && <Check className="w-3 h-3 ml-0.5" />}
        </button>

        <button
          type="button"
          onClick={() => handleRoleSwitch('admin')}
          disabled={Boolean(switchingRole)}
          className={cn(
            'inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer disabled:opacity-50',
            currentRole === 'admin'
              ? 'bg-intelligence-600 text-white shadow-2xs font-bold'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
          )}
        >
          {switchingRole === 'admin' ? (
            <Loader2 className="w-3 h-3 animate-spin text-white" />
          ) : (
            <ShieldCheck className="w-3 h-3" />
          )}
          <span>{switchingRole === 'admin' ? 'Memuat...' : 'Admin Demo'}</span>
          {currentRole === 'admin' && !switchingRole && <Check className="w-3 h-3 ml-0.5" />}
        </button>
      </div>
    </aside>
  );
};
