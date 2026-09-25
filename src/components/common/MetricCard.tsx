import React from 'react';
import { cn } from '../../lib/utils';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  colorScheme?: 'brand' | 'growth' | 'intelligence' | 'endorse' | 'revision';
  badge?: string;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  icon: Icon,
  colorScheme = 'brand',
  badge,
  className,
}) => {
  const schemeStyles = {
    brand: {
      iconBg: 'bg-brand-50 text-brand-600',
      badge: 'bg-brand-50 text-brand-700 border-brand-200',
    },
    growth: {
      iconBg: 'bg-growth-50 text-growth-600',
      badge: 'bg-growth-50 text-growth-700 border-growth-200',
    },
    intelligence: {
      iconBg: 'bg-intelligence-50 text-intelligence-600',
      badge: 'bg-intelligence-50 text-intelligence-700 border-intelligence-200',
    },
    endorse: {
      iconBg: 'bg-endorse-50 text-endorse-600',
      badge: 'bg-endorse-50 text-endorse-700 border-endorse-200',
    },
    revision: {
      iconBg: 'bg-revision-50 text-revision-600',
      badge: 'bg-revision-50 text-revision-700 border-revision-200',
    },
  };

  const currentScheme = schemeStyles[colorScheme];

  return (
    <div
      className={cn(
        'bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs hover:border-slate-300 transition-all flex flex-col justify-between',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500 tracking-wide uppercase">{label}</p>
          <p className="text-2xl sm:text-3xl font-bold text-slate-900 mt-1.5 tracking-tight">{value}</p>
        </div>
        <div className={cn('p-2.5 rounded-lg shrink-0', currentScheme.iconBg)}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      {(subtext || badge) && (
        <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
          {subtext && <span className="text-slate-500 truncate">{subtext}</span>}
          {badge && (
            <span className={cn('px-2 py-0.5 rounded-md font-medium border text-[11px]', currentScheme.badge)}>
              {badge}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
