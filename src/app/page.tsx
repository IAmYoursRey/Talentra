'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../services/auth.service';
import { CircularLogoSpinner } from '../components/common/CircularLogoSpinner';

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
    <div
      role="status"
      aria-label="Mengarahkan ke aplikasi TALENTRA.ID..."
      className="min-h-screen bg-[#FCFBFF] flex flex-col items-center justify-center p-6 select-none animate-in fade-in duration-150"
    >
      <div className="relative flex flex-col items-center max-w-sm text-center space-y-5">
        <CircularLogoSpinner size="lg" />
        <div className="space-y-1.5">
          <h2 className="text-base font-extrabold text-[#261331] tracking-tight">
            Mengarahkan ke TALENTRA.ID...
          </h2>
          <p className="text-xs text-[#6F607D]">
            Memeriksa autentikasi dan hak akses akun Anda.
          </p>
        </div>
        <div className="w-48 h-1.5 bg-purple-100 rounded-full overflow-hidden relative">
          <div className="absolute top-0 bottom-0 left-0 w-2/3 bg-gradient-to-r from-[#6D28D9] to-[#C084FC] rounded-full animate-indeterminate" />
        </div>
      </div>
    </div>
  );
}
