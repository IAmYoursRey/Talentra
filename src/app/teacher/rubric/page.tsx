'use client';

import React, { useState, useEffect } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { BookOpen, CheckCircle2, Clock, Sparkles } from 'lucide-react';

interface RubricRow {
  dimension: string;
  score1: string;
  score3: string;
  score5: string;
}

export default function TeacherRubricPage() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 200);
    return () => clearTimeout(timer);
  }, []);

  const rubrics: RubricRow[] = [
    {
      dimension: 'Initiative',
      score1: 'Perlu dorongan',
      score3: 'Mandiri',
      score5: 'Proaktif',
    },
    {
      dimension: 'Collaboration',
      score1: 'Kontribusi minim',
      score3: 'Bekerja efektif',
      score5: 'Mengangkat tim',
    },
    {
      dimension: 'Communication',
      score1: 'Pesan kurang jelas',
      score3: 'Cukup terstruktur',
      score5: 'Jelas & adaptif',
    },
    {
      dimension: 'Responsibility',
      score1: 'Sering lalai',
      score3: 'Tugas selesai',
      score5: 'Konsisten',
    },
    {
      dimension: 'Resilience',
      score1: 'Mudah berhenti',
      score3: 'Mencoba ulang',
      score5: 'Adaptif',
    },
  ];

  return (
    <AppShell pageTitle="Rubrik Soft Skill" expectedRole="teacher" isPageLoading={isLoading}>
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              Rubrik Soft Skill
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Panduan skor konsisten 1–5 untuk evidence non-fisik.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FAF5FF] border border-[#E9E1F4] text-[#A78BFA] font-bold text-xs shadow-xs self-start sm:self-auto">
            <Clock className="w-3.5 h-3.5" />
            <span>18 menunggu</span>
          </div>
        </div>

        {/* Main Rubrik Table Card */}
        <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 sm:p-8 shadow-[0_4px_16px_rgba(76,29,149,0.06)]">
          <div className="mb-6">
            <h2 className="text-lg font-extrabold text-[#261331]">Rubrik Validator</h2>
            <p className="text-xs text-[#6F607D] mt-1">
              Gunakan deskriptor perilaku agar penilaian antar-guru tetap konsisten.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#FDFBFF] rounded-xl text-xs font-bold text-[#6F607D]">
                  <th className="py-3 px-4 rounded-l-xl">Dimensi</th>
                  <th className="py-3 px-4">Skor 1</th>
                  <th className="py-3 px-4">Skor 3</th>
                  <th className="py-3 px-4 rounded-r-xl">Skor 5</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E9E1F4] text-xs">
                {rubrics.map((r) => (
                  <tr key={r.dimension} className="hover:bg-purple-50/30 transition-colors">
                    <td className="py-4 px-4 font-bold text-[#261331]">{r.dimension}</td>
                    <td className="py-4 px-4 text-[#6F607D] font-medium">{r.score1}</td>
                    <td className="py-4 px-4 text-[#6F607D] font-medium">{r.score3}</td>
                    <td className="py-4 px-4 text-[#6F607D] font-medium">{r.score5}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Footer Note */}
          <div className="mt-8 p-3 rounded-xl bg-[#F7F2FF] border border-purple-100 text-center">
            <p className="text-xs font-bold text-[#6D28D9]">
              Skor rubrik disimpan bersama keputusan validasi dan menjadi sinyal rekomendasi.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
