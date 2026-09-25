import React from 'react';
import { SoftSkillRubricDimension, RubricAssessment } from '../../types/review.types';
import { RUBRIC_LEVEL_LABELS } from '../../mocks/soft-skills-rubric.mock';
import { cn } from '../../lib/utils';
import { Award } from 'lucide-react';

interface SoftSkillRubricFormProps {
  dimensions: SoftSkillRubricDimension[];
  values: Record<string, 1 | 2 | 3 | 4 | 5>;
  onChange: (dimensionId: string, value: 1 | 2 | 3 | 4 | 5) => void;
  className?: string;
}

export const SoftSkillRubricForm: React.FC<SoftSkillRubricFormProps> = ({
  dimensions,
  values,
  onChange,
  className,
}) => {
  return (
    <div className={cn('space-y-6', className)}>
      <div className="flex items-center gap-2.5 pb-2 border-b border-slate-100">
        <div className="w-8 h-8 rounded-lg bg-growth-50 text-growth-700 flex items-center justify-center shrink-0">
          <Award className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-slate-900">Penilaian Rubrik Kompetensi & Karakter</h3>
          <p className="text-xs text-slate-500">
            Observasi perkembangan kompetensi siswa berdasarkan bukti karya yang diajukan (Skala 1–5).
          </p>
        </div>
      </div>

      <div className="space-y-5">
        {dimensions.map((dim) => {
          const currentValue = values[dim.id] || 3;
          const levelDescription = dim.levels[currentValue];

          return (
            <div key={dim.id} className="p-4 rounded-xl border border-slate-200 bg-white shadow-2xs space-y-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <label htmlFor={`rubric-${dim.id}`} className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                    {dim.name}
                  </label>
                  <p className="text-xs text-slate-500 mt-0.5">{dim.description}</p>
                </div>
                <div className="px-2.5 py-1 rounded-md bg-growth-50 border border-growth-200 text-growth-800 text-xs font-bold shrink-0">
                  Nilai: {currentValue} / 5
                </div>
              </div>

              {/* Slider Input 1-5 */}
              <div className="space-y-1.5 pt-1">
                <input
                  id={`rubric-${dim.id}`}
                  type="range"
                  min={1}
                  max={5}
                  step={1}
                  value={currentValue}
                  onChange={(e) => onChange(dim.id, parseInt(e.target.value, 10) as 1 | 2 | 3 | 4 | 5)}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-growth-600 focus:outline-none focus:ring-2 focus:ring-growth-500"
                  aria-valuemin={1}
                  aria-valuemax={5}
                  aria-valuenow={currentValue}
                  aria-valuetext={levelDescription}
                />
                <div className="flex justify-between text-[11px] text-slate-400 font-medium px-0.5">
                  <span>1 (Belum)</span>
                  <span>2 (Mulai)</span>
                  <span>3 (Konsisten)</span>
                  <span>4 (Kuat)</span>
                  <span>5 (Menonjol)</span>
                </div>
              </div>

              {/* Textual Meaning Display */}
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 flex items-start gap-2">
                <span className="text-xs font-bold text-growth-700 shrink-0">
                  {RUBRIC_LEVEL_LABELS[currentValue]}:
                </span>
                <span className="text-xs text-slate-600 leading-relaxed">
                  {levelDescription}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
