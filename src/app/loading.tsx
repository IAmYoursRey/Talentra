import React from 'react';
import { Sparkles } from 'lucide-react';
import { CircularLogoSpinner } from '../components/common/CircularLogoSpinner';

export default function GlobalLoading() {
  return (
    <div
      role="status"
      aria-label="Memuat aplikasi TALENTRA.ID..."
      className="fixed inset-0 z-50 bg-[#FCFBFF]/95 backdrop-blur-md flex flex-col items-center justify-center p-6 select-none animate-in fade-in duration-150"
    >
      <div className="relative flex flex-col items-center max-w-sm text-center space-y-5">
        {/* Circular Logo Spinner conforming to National Standards */}
        <CircularLogoSpinner size="lg" />

        {/* Text and animated status */}
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-50 border border-purple-200 text-[#6D28D9] text-[11px] font-bold">
            <Sparkles className="w-3.5 h-3.5 text-[#8B5CF6] animate-spin" style={{ animationDuration: '3s' }} />
            <span>TALENTRA.ID</span>
          </div>
          <h2 className="text-base font-extrabold text-[#261331] tracking-tight">
            Memuat Halaman...
          </h2>
          <p className="text-xs text-[#6F607D]">
            Menyiapkan data portofolio, analitik, dan sesi terverifikasi.
          </p>
        </div>

        {/* Shimmering Progress Bar */}
        <div className="w-48 h-1.5 bg-purple-100 rounded-full overflow-hidden relative">
          <div className="absolute top-0 bottom-0 left-0 w-2/3 bg-gradient-to-r from-[#6D28D9] to-[#C084FC] rounded-full animate-indeterminate" />
        </div>
      </div>
    </div>
  );
}
