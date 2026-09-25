import React from 'react';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { cn } from '../../lib/utils';
import Link from 'next/link';

interface ForbiddenStateProps {
  requiredRole?: string;
  currentRole?: string;
  onSwitchRole?: () => void;
  className?: string;
}

export const ForbiddenState: React.FC<ForbiddenStateProps> = ({
  requiredRole,
  currentRole,
  onSwitchRole,
  className,
}) => {
  return (
    <div
      role="alert"
      className={cn(
        'rounded-2xl border border-slate-200 bg-white p-8 sm:p-12 text-center max-w-lg mx-auto shadow-xs my-8',
        className
      )}
    >
      <div className="w-14 h-14 rounded-2xl bg-revision-50 text-revision-600 flex items-center justify-center mx-auto mb-4 border border-revision-200">
        <ShieldAlert className="w-7 h-7" />
      </div>
      <h2 className="text-xl font-bold text-slate-900 tracking-tight">Akses Halaman Dibatasi</h2>
      <p className="text-sm text-slate-600 mt-2 mb-6 leading-relaxed">
        Halaman ini memerlukan hak akses <strong>{requiredRole || 'khusus'}</strong>. Peran aktif Anda saat ini adalah{' '}
        <strong>{currentRole || 'pengguna'}</strong>.
      </p>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        {onSwitchRole && (
          <button
            type="button"
            onClick={onSwitchRole}
            className="w-full sm:w-auto inline-flex items-center justify-center px-4 py-2.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-medium text-sm transition-colors shadow-xs"
          >
            Beralih ke Demo {requiredRole}
          </button>
        )}
        <Link
          href="/"
          className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium text-sm transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Kembali ke Beranda</span>
        </Link>
      </div>
    </div>
  );
};
