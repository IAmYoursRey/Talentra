import React, { useState, useMemo } from 'react';
import { CanonicalTag } from '../../types/portfolio.types';
import { TagChip } from '../common/TagChip';
import { Search, AlertCircle, CheckCircle } from 'lucide-react';
import { cn } from '../../lib/utils';

interface TagSelectorProps {
  availableTags: CanonicalTag[];
  selectedTagIds: string[];
  onChange: (newSelectedTagIds: string[]) => void;
  minTags?: number;
  maxTags?: number;
  className?: string;
}

export const TagSelector: React.FC<TagSelectorProps> = ({
  availableTags,
  selectedTagIds,
  onChange,
  minTags = 3,
  maxTags = 5,
  className,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const count = selectedTagIds.length;
  const isSatisfied = count >= minTags && count <= maxTags;
  const isTooFew = count < minTags;
  const isMaxReached = count >= maxTags;

  const filteredTags = useMemo(() => {
    if (!searchQuery.trim()) return availableTags;
    const q = searchQuery.toLowerCase().trim();
    return availableTags.filter(
      (t) => t.label.toLowerCase().includes(q) || t.category.toLowerCase().includes(q)
    );
  }, [availableTags, searchQuery]);

  const handleToggleTag = (tagId: string) => {
    if (selectedTagIds.includes(tagId)) {
      onChange(selectedTagIds.filter((id) => id !== tagId));
    } else {
      if (selectedTagIds.length >= maxTags) {
        return; // Max reached
      }
      onChange([...selectedTagIds, tagId]);
    }
  };

  const handleRemoveTag = (tagId: string) => {
    onChange(selectedTagIds.filter((id) => id !== tagId));
  };

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center justify-between flex-wrap gap-2">
        <label className="block text-sm font-semibold text-slate-800">
          Tag Kompetensi & Keahlian <span className="text-reject-500">*</span>
        </label>
        <div
          className={cn(
            'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border transition-colors',
            isSatisfied
              ? 'bg-endorse-50 text-endorse-700 border-endorse-300'
              : 'bg-revision-50 text-revision-700 border-revision-300'
          )}
        >
          {isSatisfied ? <CheckCircle className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
          <span>
            {count}/{maxTags} skill tags dipilih
          </span>
        </div>
      </div>

      <p className="text-xs text-slate-500">
        Pilih minimal <strong>{minTags}</strong> dan maksimal <strong>{maxTags}</strong> tag kanonikal yang paling mencerminkan karya ini.
      </p>

      {/* Selected Tags Display */}
      {selectedTagIds.length > 0 && (
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
          <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider mb-2">
            Tag Terpilih ({selectedTagIds.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {selectedTagIds.map((id) => {
              const tag = availableTags.find((t) => t.id === id);
              return (
                <TagChip
                  key={id}
                  label={tag?.label || id}
                  category={tag?.category}
                  removable
                  onRemove={() => handleRemoveTag(id)}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Validation Message */}
      {isTooFew && count > 0 && (
        <p className="text-xs text-revision-600 flex items-center gap-1 font-medium">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>Silakan pilih minimal {minTags - count} tag lagi untuk memenuhi syarat pengajuan.</span>
        </p>
      )}
      {isMaxReached && (
        <p className="text-xs text-slate-500 italic">
          Batas maksimal ({maxTags} tag) telah tercapai. Hapus salah satu tag untuk memilih yang lain.
        </p>
      )}

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Cari tag keahlian (contoh: Web, UI/UX, Leadership)..."
          className="w-full pl-9 pr-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors"
        />
      </div>

      {/* Available Tags Cloud */}
      <div className="max-h-48 overflow-y-auto p-3 border border-slate-200 rounded-xl bg-white space-y-1.5">
        <div className="flex flex-wrap gap-1.5">
          {filteredTags.map((tag) => {
            const isSelected = selectedTagIds.includes(tag.id);
            const isDisabled = !isSelected && isMaxReached;
            return (
              <button
                type="button"
                key={tag.id}
                onClick={() => handleToggleTag(tag.id)}
                disabled={isDisabled}
                className={cn(
                  'text-xs px-2.5 py-1.5 rounded-lg border font-medium transition-all text-left flex items-center gap-1.5',
                  isSelected
                    ? 'bg-brand-500 text-white border-brand-600 shadow-2xs'
                    : isDisabled
                    ? 'bg-slate-50 text-slate-300 border-slate-100 cursor-not-allowed'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                )}
              >
                <span>{tag.label}</span>
                {isSelected && <span className="text-[10px]">✓</span>}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
