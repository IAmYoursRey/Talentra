'use client';

import React from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { ShieldCheck, Sparkles, TrendingUp } from 'lucide-react';
import { cn } from '../../../lib/utils';

interface HeatmapRow {
  grade: string;
  coding: number;
  communication: number;
  leadership: number;
  creative: number;
  analysis: number;
}

export default function AdminHeatmapPage() {
  const data: HeatmapRow[] = [
    {
      grade: 'Kelas X',
      coding: 58,
      communication: 48,
      leadership: 39,
      creative: 42,
      analysis: 35,
    },
    {
      grade: 'Kelas XI',
      coding: 67,
      communication: 56,
      leadership: 45,
      creative: 49,
      analysis: 41,
    },
    {
      grade: 'Kelas XII',
      coding: 76,
      communication: 64,
      leadership: 53,
      creative: 47,
      analysis: 44,
    },
  ];

  const getHeatmapCellBg = (value: number) => {
    if (value >= 65) return 'tal-btn-primary shadow-xs';
    if (value >= 50) return 'bg-[#A78BFA] text-white';
    if (value >= 40) return 'bg-[#C4B5FD] text-[#261331]';
    return 'bg-[#DDD6FE] text-[#261331]';
  };

  return (
    <AppShell pageTitle="Talent Heatmap" expectedRole="admin">
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header matching 18-Admin-Heatmap-HF.svg */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              Talent Heatmap
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Analisis agregat talenta berdasarkan kelas dan domain.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#F3E8FF] border border-purple-200 text-[#6D28D9] font-bold text-xs shadow-xs self-start sm:self-auto">
            <span>2026 • Semester 1</span>
          </div>
        </div>

        {/* Heatmap Card */}
        <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 sm:p-8 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-8">
          <div>
            <h2 className="text-lg font-extrabold text-[#261331]">Heatmap by Grade & Domain</h2>
            <p className="text-xs text-[#6F607D] mt-1">
              Tidak menampilkan ranking individu.
            </p>
          </div>

          <div className="overflow-x-auto">
            <div className="min-w-[640px] space-y-4">
              {/* Columns Header */}
              <div className="grid grid-cols-6 gap-3 text-center text-xs font-bold text-[#6F607D] pb-2">
                <div className="text-left pl-2">Cohort</div>
                <div>Coding</div>
                <div>Communication</div>
                <div>Leadership</div>
                <div>Creative</div>
                <div>Analysis</div>
              </div>

              {/* Rows */}
              {data.map((row) => (
                <div key={row.grade} className="grid grid-cols-6 gap-3 items-center">
                  <div className="font-extrabold text-[#261331] text-sm pl-2">{row.grade}</div>
                  <div
                    className={cn(
                      'h-16 rounded-2xl flex items-center justify-center font-extrabold text-lg transition-transform hover:scale-[1.03] select-none',
                      getHeatmapCellBg(row.coding)
                    )}
                  >
                    {row.coding}%
                  </div>
                  <div
                    className={cn(
                      'h-16 rounded-2xl flex items-center justify-center font-extrabold text-lg transition-transform hover:scale-[1.03] select-none',
                      getHeatmapCellBg(row.communication)
                    )}
                  >
                    {row.communication}%
                  </div>
                  <div
                    className={cn(
                      'h-16 rounded-2xl flex items-center justify-center font-extrabold text-lg transition-transform hover:scale-[1.03] select-none',
                      getHeatmapCellBg(row.leadership)
                    )}
                  >
                    {row.leadership}%
                  </div>
                  <div
                    className={cn(
                      'h-16 rounded-2xl flex items-center justify-center font-extrabold text-lg transition-transform hover:scale-[1.03] select-none',
                      getHeatmapCellBg(row.creative)
                    )}
                  >
                    {row.creative}%
                  </div>
                  <div
                    className={cn(
                      'h-16 rounded-2xl flex items-center justify-center font-extrabold text-lg transition-transform hover:scale-[1.03] select-none',
                      getHeatmapCellBg(row.analysis)
                    )}
                  >
                    {row.analysis}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Insight Banner */}
          <div className="p-4 rounded-xl bg-[#F3E8FF] border border-purple-200 flex items-center gap-3">
            <Sparkles className="w-4 h-4 text-[#6D28D9] shrink-0" />
            <p className="text-xs font-bold text-[#6D28D9]">
              Insight: Technology & Coding tumbuh paling cepat pada cohort XII.
            </p>
          </div>

          {/* Privacy Guarantee Note */}
          <div className="p-3 rounded-xl bg-[#F7F2FF] border border-purple-100 text-center">
            <p className="text-xs font-bold text-[#6D28D9]">
              PRIVACY — hanya cohort ≥ 5, tanpa leaderboard siswa.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
