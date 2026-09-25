import React, { useState } from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { SkillRadarPoint } from '../../types/skill.types';
import { Table, Eye, CheckCircle2 } from 'lucide-react';
import { cn } from '../../lib/utils';

interface SkillRadarChartProps {
  data: SkillRadarPoint[];
  height?: number;
  showTextAlternative?: boolean;
  className?: string;
}

export const SkillRadarChart: React.FC<SkillRadarChartProps> = ({
  data,
  height = 320,
  showTextAlternative = true,
  className,
}) => {
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart');

  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-400 text-sm">
        Belum ada data kompetensi yang tervalidasi.
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs text-growth-700 bg-growth-50 px-2.5 py-1 rounded-full border border-growth-200">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Dihitung hanya dari bukti karya yang telah disetujui</span>
        </div>
        {showTextAlternative && (
          <button
            type="button"
            onClick={() => setViewMode(viewMode === 'chart' ? 'table' : 'chart')}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200/80 px-2.5 py-1 rounded-lg transition-colors"
            aria-label={viewMode === 'chart' ? 'Tampilkan ringkasan teks kompetensi' : 'Tampilkan radar chart visual'}
          >
            {viewMode === 'chart' ? (
              <>
                <Table className="w-3.5 h-3.5" />
                <span>Format Tabel</span>
              </>
            ) : (
              <>
                <Eye className="w-3.5 h-3.5" />
                <span>Format Radar</span>
              </>
            )}
          </button>
        )}
      </div>

      {viewMode === 'chart' ? (
        <div style={{ width: '100%', height }} aria-hidden="true">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
              <PolarGrid stroke="#E2E8F0" />
              <PolarAngleAxis
                dataKey="skill"
                tick={{ fill: '#334155', fontSize: 11, fontWeight: 500 }}
              />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#94A3B8', fontSize: 10 }} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const point = payload[0].payload as SkillRadarPoint;
                    return (
                      <div className="bg-slate-900 text-white text-xs rounded-lg p-2.5 shadow-lg space-y-1">
                        <p className="font-bold">{point.skill}</p>
                        <p className="text-growth-400">Skor: {point.score} / 100</p>
                        <p className="text-slate-300 text-[11px]">
                          {point.approvedEvidenceCount} karya terverifikasi
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Radar
                name="Kompetensi"
                dataKey="score"
                stroke="#0F8F83"
                fill="#0F8F83"
                fillOpacity={0.4}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        /* Accessible Text Table Alternative */
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] font-semibold border-b border-slate-200">
              <tr>
                <th scope="col" className="px-4 py-2.5">Dimensi Kompetensi</th>
                <th scope="col" className="px-4 py-2.5">Skor Terkalkulasi</th>
                <th scope="col" className="px-4 py-2.5">Karya Tervalidasi</th>
                <th scope="col" className="px-4 py-2.5">Tingkat Capaian</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((item) => (
                <tr key={item.skill} className="hover:bg-slate-50/70">
                  <td className="px-4 py-2.5 font-semibold text-slate-900">{item.skill}</td>
                  <td className="px-4 py-2.5 font-bold text-growth-700">{item.score} / 100</td>
                  <td className="px-4 py-2.5">{item.approvedEvidenceCount} karya</td>
                  <td className="px-4 py-2.5">
                    <span
                      className={cn(
                        'px-2 py-0.5 rounded-full text-[10px] font-semibold',
                        item.score >= 80
                          ? 'bg-endorse-50 text-endorse-700'
                          : item.score >= 60
                          ? 'bg-brand-50 text-brand-700'
                          : 'bg-slate-100 text-slate-600'
                      )}
                    >
                      {item.score >= 80 ? 'Mahir' : item.score >= 60 ? 'Menengah' : 'Dasar'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
