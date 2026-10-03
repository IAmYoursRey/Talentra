import React from 'react';
import Link from 'next/link';
import { cn } from '../../lib/utils';
import { LucideIcon, ArrowUpRight } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: LucideIcon;
  colorScheme?: 'brand' | 'growth' | 'intelligence' | 'endorse' | 'revision';
  badge?: string;
  indexNumber?: number;
  className?: string;
  href?: string;
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  icon: Icon,
  colorScheme = 'brand',
  badge,
  indexNumber,
  className,
  href,
  onClick,
}) => {
  const isInteractive = Boolean(href || onClick);

  const cardContent = (
    <>
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          {indexNumber !== undefined && (
            <span className="w-5 h-5 rounded-full bg-[#F3E8FF] text-[#6D28D9] font-extrabold text-[10px] flex items-center justify-center mb-1">
              {indexNumber}
            </span>
          )}
          <p className="text-xs font-semibold text-[#6F607D] tracking-tight">{label}</p>
          <p className="text-3xl font-extrabold text-[#261331] tracking-tight">{value}</p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {Icon && (
            <div className="p-3 rounded-xl bg-[#F7F2FF] text-[#6D28D9] border border-purple-100 group-hover:scale-105 transition-transform">
              <Icon className="w-5 h-5" />
            </div>
          )}
          {isInteractive && (
            <div className="w-6 h-6 rounded-lg bg-purple-50 text-[#6D28D9] opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
              <ArrowUpRight className="w-3.5 h-3.5" />
            </div>
          )}
        </div>
      </div>

      {(subtext || badge) && (
        <div className="mt-4 pt-3 border-t border-[#E9E1F4] flex items-center justify-between text-xs">
          {subtext && <span className="text-[#6F607D] font-medium truncate">{subtext}</span>}
          {badge && (
            <span className="px-2.5 py-0.5 rounded-full font-bold text-[10px] bg-[#F7F2FF] text-[#6D28D9] border border-purple-100">
              {badge}
            </span>
          )}
        </div>
      )}
    </>
  );

  const baseClasses = cn(
    'bg-white rounded-[18px] border border-[#E9E1F4] p-5 sm:p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] hover:shadow-[0_8px_24px_rgba(76,29,149,0.12)] transition-all flex flex-col justify-between tal-card-hover group text-left',
    isInteractive && 'cursor-pointer hover:border-purple-300 focus-visible:ring-2 focus-visible:ring-[#8B5CF6]',
    className
  );

  if (href) {
    return (
      <Link href={href} className={baseClasses}>
        {cardContent}
      </Link>
    );
  }

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={baseClasses}>
        {cardContent}
      </button>
    );
  }

  return <div className={baseClasses}>{cardContent}</div>;
};
