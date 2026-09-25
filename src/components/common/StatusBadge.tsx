import React from 'react';
import { PortfolioStatus } from '../../types/portfolio.types';
import { CheckCircle2, Clock, AlertTriangle, XCircle, FileEdit } from 'lucide-react';
import { cn } from '../../lib/utils';

interface StatusBadgeProps {
  status: PortfolioStatus;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md', className }) => {
  const configs: Record<
    PortfolioStatus,
    { label: string; icon: React.ComponentType<{ className?: string }>; bg: string; text: string; border: string }
  > = {
    draft: {
      label: 'Draft',
      icon: FileEdit,
      bg: 'bg-slate-100',
      text: 'text-slate-700',
      border: 'border-slate-300',
    },
    submitted: {
      label: 'Menunggu Validasi',
      icon: Clock,
      bg: 'bg-brand-50',
      text: 'text-brand-700',
      border: 'border-brand-200',
    },
    revision_requested: {
      label: 'Perlu Revisi',
      icon: AlertTriangle,
      bg: 'bg-revision-50',
      text: 'text-revision-700',
      border: 'border-revision-300',
    },
    approved: {
      label: 'Disetujui',
      icon: CheckCircle2,
      bg: 'bg-endorse-50',
      text: 'text-endorse-700',
      border: 'border-endorse-300',
    },
    rejected: {
      label: 'Ditolak',
      icon: XCircle,
      bg: 'bg-reject-50',
      text: 'text-reject-700',
      border: 'border-reject-300',
    },
  };

  const config = configs[status] || configs.draft;
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs font-medium px-2.5 py-1 gap-1.5',
    lg: 'text-sm font-medium px-3 py-1.5 gap-2',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-3.5 h-3.5',
    lg: 'w-4 h-4',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border shadow-xs transition-colors font-medium',
        config.bg,
        config.text,
        config.border,
        sizeClasses[size],
        className
      )}
    >
      <Icon className={cn(iconSizes[size], 'shrink-0')} />
      <span>{config.label}</span>
    </span>
  );
};
