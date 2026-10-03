'use client';

import React from 'react';
import { cn } from '../../lib/utils';

interface CircularLogoSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const CircularLogoSpinner: React.FC<CircularLogoSpinnerProps> = ({
  size = 'md',
  className,
}) => {
  const sizeClasses = {
    sm: {
      container: 'w-12 h-12',
      badge: 'w-8 h-8 text-xs',
      border: 'border-2',
      dot: 'w-1.5 h-1.5',
    },
    md: {
      container: 'w-16 h-16',
      badge: 'w-10 h-10 text-sm',
      border: 'border-[3px]',
      dot: 'w-2 h-2',
    },
    lg: {
      container: 'w-20 h-20',
      badge: 'w-12 h-12 text-lg',
      border: 'border-4',
      dot: 'w-2.5 h-2.5',
    },
  }[size];

  return (
    <div
      role="progressbar"
      aria-label="Memuat data..."
      className={cn('relative flex items-center justify-center shrink-0 select-none', sizeClasses.container, className)}
    >
      {/* 1. Subtle glowing pulse aura */}
      <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-[#6D28D9] to-[#8B5CF6] opacity-20 blur-md animate-pulse" />

      {/* 2. Static circular track */}
      <div className={cn('absolute inset-0 rounded-full border-purple-100', sizeClasses.border)} />

      {/* 3. Pure circular spinning arc */}
      <div
        className={cn(
          'absolute inset-0 rounded-full border-transparent border-t-[#6D28D9] border-r-[#8B5CF6] animate-spin',
          sizeClasses.border
        )}
      />

      {/* 4. Center circular emblem badge with TALENTRA "T" */}
      <div
        className={cn(
          'relative rounded-full bg-gradient-to-br from-[#2E1065] via-[#4C1D95] to-[#6D28D9] flex items-center justify-center font-black text-white shadow-md shadow-purple-950/20 border border-purple-300/40 select-none',
          sizeClasses.badge
        )}
      >
        T
        {/* Status indicator dot */}
        <span
          className={cn(
            'absolute bottom-0 right-0 rounded-full bg-[#10B981] ring-2 ring-white',
            sizeClasses.dot
          )}
        />
      </div>
    </div>
  );
};
