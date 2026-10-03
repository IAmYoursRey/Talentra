import React, { useEffect, useRef } from 'react';
import { AlertTriangle, X, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'primary';
  isSubmitting?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  children?: React.ReactNode;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  description,
  confirmLabel = 'Konfirmasi',
  cancelLabel = 'Batal',
  variant = 'danger',
  isSubmitting = false,
  onConfirm,
  onCancel,
  children,
}) => {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') {
        onCancel();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const variantStyles = {
    danger: {
      btn: 'bg-reject-500 hover:bg-reject-600 text-white focus:ring-reject-500',
      icon: 'text-reject-600 bg-reject-100',
    },
    warning: {
      btn: 'bg-revision-500 hover:bg-revision-600 text-white focus:ring-revision-500',
      icon: 'text-revision-600 bg-revision-100',
    },
    primary: {
      btn: 'bg-brand-500 hover:bg-brand-600 text-white focus:ring-brand-500',
      icon: 'text-brand-600 bg-brand-100',
    },
  };

  const currentVariant = variantStyles[variant];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs transition-opacity"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
    >
      <div
        ref={dialogRef}
        className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-200 p-6 animate-in fade-in zoom-in-95 duration-150"
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center shrink-0', currentVariant.icon)}>
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 id="dialog-title" className="text-base font-bold text-slate-900">
                {title}
              </h3>
            </div>
          </div>
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            aria-label="Tutup modal"
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-sm text-slate-600 mt-3 leading-relaxed">{description}</p>

        {children && <div className="mt-4">{children}</div>}

        <div className="mt-6 flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-300"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isSubmitting}
            className={cn(
              'px-4 py-2 text-sm font-medium rounded-lg transition-colors shadow-xs focus:outline-none focus:ring-2 focus:ring-offset-1 inline-flex items-center gap-1.5',
              currentVariant.btn,
              isSubmitting && 'opacity-60 cursor-not-allowed'
            )}
          >
            {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />}
            <span>{isSubmitting ? 'Memproses...' : confirmLabel}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
