import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Gagal Memuat Data',
  message,
  onRetry,
  className,
}) => {
  return (
    <div
      role="alert"
      className={cn(
        'rounded-xl border border-reject-200 bg-reject-50/50 p-6 text-center flex flex-col items-center justify-center my-4',
        className
      )}
    >
      <div className="w-10 h-10 rounded-full bg-reject-100 flex items-center justify-center text-reject-600 mb-3">
        <AlertCircle className="w-5 h-5" />
      </div>
      <h3 className="text-sm font-semibold text-reject-900">{title}</h3>
      <p className="text-xs text-reject-700 max-w-md mt-1 mb-4 leading-relaxed">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-reject-300 hover:bg-reject-50 text-reject-800 text-xs font-medium transition-colors shadow-2xs focus:outline-none focus:ring-2 focus:ring-reject-500 focus:ring-offset-1"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Coba Lagi</span>
        </button>
      )}
    </div>
  );
};
