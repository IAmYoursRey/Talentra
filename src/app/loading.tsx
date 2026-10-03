import React from 'react';
import { Sparkles } from 'lucide-react';

export default function GlobalLoading() {
  return (
    <div
      role="status"
      aria-label="Memuat aplikasi TALENTRA.ID..."
      className="fixed inset-0 z-50 bg-[#FCFBFF]/80 backdrop-blur-md flex flex-col items-center justify-center p-6 select-none animate-in fade-in duration-150"
    >
      <div className="relative flex flex-col items-center max-w-sm text-center space-y-5">
        {/* Glowing Brand Emblem & Spinning Ring */}
        <div className="relative w-20 h-20 flex items-center justify-center">
          {/* Outer glowing pulsing ring */}
          <div className="absolute inset-0 rounded-3xl bg-gradient-to-tr from-[#6D28D9] via-[#8B5CF6] to-[#C084FC] opacity-30 blur-xl animate-pulse" />

          {/* Spinning gradient ring */}
          <div className="absolute -inset-1.5 rounded-[28px] border-2 border-transparent border-t-[#8B5CF6] border-r-[#C084FC] animate-spin" />

          {/* Central Logo Box */}
          <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-[#2E1065] via-[#4C1D95] to-[#6D28D9] flex items-center justify-center font-black text-white text-2xl shadow-xl shadow-purple-950/20 border border-purple-400/30">
            T
            <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-[#C084FC] ring-2 ring-[#2E1065]" />
          </div>
        </div>

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
