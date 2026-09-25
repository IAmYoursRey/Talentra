import React from 'react';
import { cn } from '../../lib/utils';

interface LoadingSkeletonProps {
  className?: string;
  rows?: number;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ className, rows = 3 }) => {
  return (
    <div className={cn('animate-pulse space-y-3', className)} role="status" aria-label="Memuat data...">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'bg-slate-200/80 rounded-md',
            i === 0 ? 'h-6 w-1/3 mb-4' : 'h-4',
            i === 1 ? 'w-full' : '',
            i === 2 ? 'w-4/5' : '',
            i > 2 ? 'w-2/3' : ''
          )}
        />
      ))}
      <span className="sr-only">Sedang memuat data...</span>
    </div>
  );
};
