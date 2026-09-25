import React from 'react';
import { cn } from '../../lib/utils';
import { X } from 'lucide-react';

interface TagChipProps {
  label: string;
  category?: 'technical' | 'creative' | 'leadership' | 'communication' | 'problem_solving' | 'collaboration';
  selected?: boolean;
  removable?: boolean;
  onRemove?: () => void;
  onClick?: () => void;
  size?: 'sm' | 'md';
  className?: string;
}

export const TagChip: React.FC<TagChipProps> = ({
  label,
  category,
  selected = false,
  removable = false,
  onRemove,
  onClick,
  size = 'md',
  className,
}) => {
  const categoryStyles: Record<string, string> = {
    technical: 'bg-blue-50 text-blue-700 border-blue-200',
    creative: 'bg-purple-50 text-purple-700 border-purple-200',
    leadership: 'bg-amber-50 text-amber-700 border-amber-200',
    communication: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    problem_solving: 'bg-cyan-50 text-cyan-700 border-cyan-200',
    collaboration: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  };

  const defaultCategoryStyle = category ? categoryStyles[category] : 'bg-slate-100 text-slate-700 border-slate-200';

  return (
    <span
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick();
        }
      }}
      className={cn(
        'inline-flex items-center rounded-md border font-medium transition-all select-none',
        size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-xs px-2.5 py-1',
        selected
          ? 'bg-brand-500 text-white border-brand-600 shadow-xs'
          : defaultCategoryStyle,
        onClick && 'cursor-pointer hover:opacity-90 active:scale-98 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-1',
        className
      )}
    >
      <span>{label}</span>
      {removable && onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          aria-label={`Hapus tag ${label}`}
          className="ml-1.5 p-0.5 rounded-full hover:bg-black/10 focus:outline-none focus:ring-1 focus:ring-brand-500"
        >
          <X className="w-3 h-3" />
        </button>
      )}
    </span>
  );
};
