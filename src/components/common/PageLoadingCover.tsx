'use client';

import React from 'react';
import { cn } from '../../lib/utils';
import { CircularLogoSpinner } from './CircularLogoSpinner';

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
        {/* Animated Circular Logo Spinner conforming to National Standards */}
        <CircularLogoSpinner size="lg" />

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
