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
      btn: 'tal-btn-rose',
      icon: 'text-rose-600 bg-rose-100',
    },
    warning: {
      btn: 'tal-btn-amber',
      icon: 'text-amber-600 bg-amber-100',
    },
    primary: {
      btn: 'tal-btn-primary',
      icon: 'text-purple-600 bg-purple-100',
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
            className="px-4 py-2 text-sm font-semibold rounded-xl tal-btn-secondary"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isSubmitting}
            className={cn(
              'px-5 py-2 text-sm font-bold rounded-xl inline-flex items-center gap-1.5',
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
