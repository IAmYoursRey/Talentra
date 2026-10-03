import React from 'react';
import { cn } from '../../lib/utils';
import { CircularLogoSpinner } from './CircularLogoSpinner';

interface LoadingSkeletonProps {
  className?: string;
  rows?: number;
  showSpinner?: boolean;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  className,
  rows = 3,
  showSpinner = true,
}) => {
  return (
    <div
      className={cn('space-y-4', className)}
      role="status"
      aria-label="Memuat data..."
    >
      {showSpinner && (
        <div className="flex items-center gap-3 pb-3 border-b border-purple-100/60">
          <CircularLogoSpinner size="sm" />
          <div className="space-y-0.5">
            <span className="text-xs font-bold text-[#261331] tracking-tight block">
              Memuat data...
            </span>
            <span className="text-[11px] text-[#6F607D] block">
              Menyiapkan informasi terbaru
            </span>
          </div>
        </div>
      )}

      <div className="animate-pulse space-y-3 pt-1">
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            className={cn(
              'bg-gradient-to-r from-purple-100/70 via-purple-50/90 to-purple-100/70 rounded-xl',
              i === 0 ? 'h-5 w-1/3 mb-3' : 'h-3.5',
              i === 1 ? 'w-full' : '',
              i === 2 ? 'w-4/5' : '',
              i > 2 ? 'w-2/3' : ''
            )}
          />
        ))}
      </div>
      <span className="sr-only">Sedang memuat data...</span>
    </div>
  );
};
