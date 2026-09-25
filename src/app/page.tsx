'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../services/auth.service';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    authService.getCurrentSession().then((session) => {
      if (session.isAuthenticated) {
        if (session.role === 'student') router.replace('/student');
        else if (session.role === 'teacher') router.replace('/teacher');
        else if (session.role === 'admin') router.replace('/admin');
      } else {
        router.replace('/login');
      }
    });
  }, [router]);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="text-center space-y-3">
        <div className="w-12 h-12 rounded-xl bg-brand-500 text-white font-extrabold text-2xl flex items-center justify-center mx-auto shadow-sm animate-pulse">
          T
        </div>
        <p className="text-sm font-semibold text-slate-700">Mengarahkan ke TALENTRA.ID...</p>
      </div>
    </div>
  );
}
