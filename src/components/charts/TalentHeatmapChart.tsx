import React from 'react';
import { TalentHeatmapDimension, TalentHeatmapItem } from '../../types/analytics.types';
import { ShieldAlert, Info } from 'lucide-react';
import { cn } from '../../lib/utils';

interface TalentHeatmapChartProps {
  dimensions?: TalentHeatmapDimension[];
  items?: TalentHeatmapItem[];
  isCohortSuppressed?: boolean;
  suppressionReason?: string;
  className?: string;
}

export const TalentHeatmapChart: React.FC<TalentHeatmapChartProps> = ({
  dimensions,
  items,
  isCohortSuppressed = false,
  suppressionReason,
  className,
}) => {
  // If the entire cohort is suppressed due to privacy threshold (<5 unique students)
  if (isCohortSuppressed) {
    return (
      <div
        role="alert"
        className={cn(
          'p-6 rounded-2xl border border-amber-200 bg-amber-50/70 text-center flex flex-col items-center justify-center space-y-2',
          className
        )}
      >
        <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-700">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <h4 className="text-sm font-bold text-amber-900">Privasi Kohor Dilindungi</h4>
        <p className="text-xs text-amber-800 max-w-md leading-relaxed">
          Data tidak ditampilkan karena jumlah siswa dalam kelompok terlalu sedikit (ambang batas privasi &ge; 5 siswa).
        </p>
      </div>
    );
  }

  // Phase 6 Real Dimensions display
  if (dimensions && dimensions.length > 0) {
    return (
      <div className={cn('space-y-4', className)}>
        {/* Footnote / Explanation Header */}
        <div className="flex items-start gap-2 p-3 bg-slate-50 border border-slate-200/80 rounded-xl text-xs text-slate-600">
          <Info className="w-4 h-4 text-intelligence-600 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <p className="font-semibold text-slate-800">Berdasarkan karya yang telah divalidasi guru.</p>
            <p className="text-[11px] text-slate-500">
              Coverage menunjukkan proporsi siswa dalam kelompok yang memiliki setidaknya satu bukti karya tervalidasi pada dimensi tersebut.
            </p>
          </div>
        </div>

        <div className="space-y-3.5">
          {dimensions.map((dim) => {
            if (dim.suppressed) {
              return (
                <div
                  key={dim.dimension}
                  className="p-4 rounded-xl border border-dashed border-amber-200 bg-amber-50/40 flex items-center justify-between"
                >
                  <div>
                    <span className="text-sm font-bold text-slate-800">{dim.displayName}</span>
                    <p className="text-[11px] text-amber-700 mt-0.5">
                      Data tidak ditampilkan karena jumlah siswa dalam kelompok terlalu sedikit.
                    </p>
                  </div>
                  <span className="text-[10px] font-semibold text-amber-700 bg-amber-100 px-2 py-0.5 rounded">
                    Tersupresi
                  </span>
                </div>
              );
            }

            const coverage = dim.coverageRate ?? 0;
            const meanIndex = dim.meanEvidenceIndex ?? 0;
            const studentsWith = dim.studentsWithEvidence ?? 0;
            const eligible = dim.eligibleStudents ?? 0;

            const getBarColor = (d: string) => {
              if (d.includes('digital')) return 'bg-brand-500';
              if (d.includes('problem')) return 'bg-cyan-500';
              if (d.includes('creativity')) return 'bg-purple-500';
              if (d.includes('leadership')) return 'bg-amber-500';
              if (d.includes('collaboration')) return 'bg-growth-600';
              return 'bg-intelligence-600';
            };

            return (
              <div
                key={dim.dimension}
                className="p-4 rounded-xl border border-slate-200/80 bg-white shadow-2xs hover:border-slate-300 transition-all space-y-2.5"
              >
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <span className="text-sm font-bold text-slate-800">{dim.displayName}</span>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {coverage > 0
                        ? `${coverage.toFixed(1)}% memiliki bukti tervalidasi — ${dim.displayName}`
                        : 'Belum ada bukti tervalidasi pada kohor ini'}
                    </p>
                  </div>

                  <div className="text-right">
                    <span className="text-xs font-bold text-slate-900">{coverage.toFixed(1)}%</span>
                    <p className="text-[10px] text-slate-400">
                      {studentsWith} dari {eligible} siswa
                    </p>
                  </div>
                </div>

                {/* Coverage Bar */}
                <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                  <div
                    className={cn('h-2.5 rounded-full transition-all duration-500', getBarColor(dim.dimension))}
                    style={{ width: `${Math.min(100, Math.max(0, coverage))}%` }}
                  />
                </div>

                {/* Sub metrics: Mean Evidence Index */}
                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-100">
                  <span>Indeks Bukti Rata-rata Kohor:</span>
                  <span className="font-semibold text-slate-800 font-mono">
                    {meanIndex.toFixed(1)} / 100
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Legacy fallback for items
  if (items && items.length > 0) {
    return (
      <div className={cn('space-y-4', className)}>
        <div className="space-y-4">
          {items.map((item) => (
            <div
              key={item.category}
              className="p-4 rounded-xl border border-slate-200/80 bg-white shadow-2xs hover:border-slate-300 transition-all"
            >
              <div className="flex items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-800">{item.category}</span>
                  <span className="inline-flex items-center text-[11px] font-semibold text-endorse-600 bg-endorse-50 px-1.5 py-0.5 rounded">
                    +{item.growth}%
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-500">{item.studentCount} siswa</span>
                  <span className="font-bold text-slate-900">{item.percentage}%</span>
                </div>
              </div>

              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                <div
                  className="h-2.5 rounded-full bg-brand-500 transition-all duration-500"
                  style={{ width: `${item.percentage}%` }}
                />
              </div>

              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {item.topSkills.map((skill) => (
                  <span
                    key={skill}
                    className="text-[11px] bg-slate-50 text-slate-600 border border-slate-200/70 px-2 py-0.5 rounded-md"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 text-center text-xs text-slate-500">
      Tidak ada data analitik talenta yang tersedia untuk kelompok ini.
    </div>
  );
};
