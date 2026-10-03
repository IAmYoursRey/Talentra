'use client';

import React from 'react';
import { cn } from '../../lib/utils';

interface PageLoadingCoverProps {
  isVisible?: boolean;
  message?: string;
  subMessage?: string;
  className?: string;
}

export const PageLoadingCover: React.FC<PageLoadingCoverProps> = ({
  isVisible = true,
  message = 'Memuat Halaman...',
  subMessage = 'Menyiapkan data portofolio dan asesmen terbaru.',
  className,
}) => {
  if (!isVisible) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={message}
      className={cn(
        'absolute inset-0 z-40 flex flex-col items-center justify-center p-6 bg-[#FCFBFF]/95 backdrop-blur-md select-none transition-all duration-200 animate-in fade-in',
        className
      )}
    >
      <div className="relative flex flex-col items-center max-w-sm text-center space-y-4">
        {/* Animated TALENTRA Logo Spinner */}
        <div className="relative w-20 h-20 flex items-center justify-center">
          {/* Pulsating glowing aura */}
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-[#6D28D9] via-[#8B5CF6] to-[#C084FC] opacity-35 blur-xl animate-pulse" />
          
          {/* Outer reverse subtle orbit ring */}
          <div className="absolute -inset-3 rounded-full border border-dashed border-purple-300/60 animate-spin-reverse" />

          {/* Primary spinning gradient ring */}
          <div className="absolute -inset-1.5 rounded-[22px] border-2 border-transparent border-t-[#8B5CF6] border-r-[#C084FC] animate-spin" />
          
          {/* Outer glowing border ring */}
          <div className="absolute -inset-0.5 rounded-[20px] border border-purple-200/50" />

          {/* Central Logo Box */}
          <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-[#2E1065] via-[#4C1D95] to-[#6D28D9] flex items-center justify-center font-black text-white text-2xl shadow-xl shadow-purple-950/25 border border-purple-400/40">
            T
            <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-[#C084FC] ring-2 ring-[#2E1065] animate-ping" />
            <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-[#C084FC] ring-2 ring-[#2E1065]" />
          </div>
        </div>

        {/* Text descriptions */}
        <div className="space-y-1">
          <h3 className="text-sm font-extrabold text-[#261331] tracking-tight">
            {message}
          </h3>
          <p className="text-xs text-[#6F607D] max-w-xs">
            {subMessage}
          </p>
        </div>

        {/* Indeterminate linear loading bar */}
        <div className="w-40 h-1.5 bg-purple-100 rounded-full overflow-hidden relative shadow-inner">
          <div className="absolute top-0 bottom-0 left-0 w-1/2 bg-gradient-to-r from-[#6D28D9] via-[#8B5CF6] to-[#C084FC] rounded-full animate-indeterminate" />
        </div>
      </div>
    </div>
  );
};
