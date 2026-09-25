'use client';

import React, { useState, useEffect } from 'react';
import { authService } from '../../services/auth.service';
import { UserRole, UserProfile } from '../../types/auth.types';
import { useRouter } from 'next/navigation';
import { Sparkles, User, GraduationCap, ShieldCheck, Check } from 'lucide-react';
import { cn } from '../../lib/utils';

export const DemoAccessBanner: React.FC = () => {
  const router = useRouter();
  const [currentRole, setCurrentRole] = useState<UserRole>('student');
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);

  // In production or when explicitly disabled, completely suppress demo banner
  const isDemoAllowed =
    process.env.NEXT_PUBLIC_ENABLE_DEMO_AUTH !== 'false' &&
    process.env.NODE_ENV !== 'production';

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

  if (!isDemoAllowed) {
    return null;
  }

  const handleRoleSwitch = async (role: UserRole) => {
    try {
      const res = await authService.demoLogin(role);
      router.push(res.redirectTo);
    } catch {
      // Incurred error during role switch
    }
  };

  return (
    <aside
      aria-label="Mode demonstrasi pengembang"
      className="bg-slate-900 text-slate-100 text-xs py-2 px-3 sm:px-6 flex flex-wrap items-center justify-between gap-2.5 border-b border-slate-800 shadow-xs z-40 sticky top-0"
    >
      <div className="flex items-center gap-2">
        <span className="flex items-center gap-1 font-semibold text-brand-400 bg-brand-950/80 px-2 py-0.5 rounded border border-brand-800/60">
          <Sparkles className="w-3 h-3" />
          <span>DEMO ACCESS TOOL</span>
        </span>
        <span className="text-slate-400 hidden sm:inline">|</span>
        <span className="text-slate-300 hidden md:inline">
          Aktif: <strong>{currentUser?.name || 'Alya Rahma'}</strong> ({currentUser?.maskedIdentifier})
        </span>
      </div>

      <div className="flex items-center gap-1.5 flex-wrap">
        <span className="text-slate-400 text-[11px] mr-1 hidden xs:inline">Ganti Peran:</span>
        <button
          type="button"
          onClick={() => handleRoleSwitch('student')}
          className={cn(
            'inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium transition-all',
            currentRole === 'student'
              ? 'bg-brand-500 text-white shadow-2xs font-semibold'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
          )}
        >
          <User className="w-3 h-3" />
          <span>Demo Siswa</span>
          {currentRole === 'student' && <Check className="w-3 h-3 ml-0.5" />}
        </button>

        <button
          type="button"
          onClick={() => handleRoleSwitch('teacher')}
          className={cn(
            'inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium transition-all',
            currentRole === 'teacher'
              ? 'bg-growth-600 text-white shadow-2xs font-semibold'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
          )}
        >
          <GraduationCap className="w-3 h-3" />
          <span>Demo Guru</span>
          {currentRole === 'teacher' && <Check className="w-3 h-3 ml-0.5" />}
        </button>

        <button
          type="button"
          onClick={() => handleRoleSwitch('admin')}
          className={cn(
            'inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium transition-all',
            currentRole === 'admin'
              ? 'bg-intelligence-600 text-white shadow-2xs font-semibold'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
          )}
        >
          <ShieldCheck className="w-3 h-3" />
          <span>Demo Admin</span>
          {currentRole === 'admin' && <Check className="w-3 h-3 ml-0.5" />}
        </button>
      </div>
    </aside>
  );
};
