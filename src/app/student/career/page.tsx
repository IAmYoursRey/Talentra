'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
  Compass,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  ChevronRight,
  HelpCircle,
} from 'lucide-react';
import { AppShell } from '../../../components/layout/AppShell';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';
import { recommendationService } from '../../../services/recommendation.service';
import { RecommendationResponse } from '../../../types/recommendation.types';

export default function StudentCareerPage() {
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPathIndex, setSelectedPathIndex] = useState(0);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await recommendationService.getStudentRecommendations();
      setData(res);
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const defaultPaths = [
    {
      rank: '01',
      title: 'S1 Sistem Informasi',
      category: 'Logika • produk • komunikasi',
      match: 92,
      explanation: '5 evidence WebDev + 4 problem solving + komunikasi guru rata-rata 4/5.',
    },
    {
      rank: '02',
      title: 'Product / UI Designer',
      category: 'Desain • presentasi • kreativitas',
      match: 84,
      explanation: '4 evidence Creative Design + 3 WebDev + presentasi publik.',
    },
    {
      rank: '03',
      title: 'D4 Teknologi Rekayasa',
      category: 'Build • analisis • problem solving',
      match: 79,
      explanation: 'Robot Line Follower + 3 analisis teknis tervalidasi.',
    },
  ];

  const currentRationale = defaultPaths[selectedPathIndex] || defaultPaths[0];

  return (
    <AppShell pageTitle="Career Path" expectedRole="student">
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header matching 10-Student-Career-HF.svg */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              Career Path
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Rekomendasi studi dan karier yang dapat ditelusuri ke evidence.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FAF5FF] border border-[#E9E1F4] text-[#A78BFA] font-bold text-xs shadow-xs self-start sm:self-auto">
            <span>Semester 5</span>
          </div>
        </div>

        {/* Top Notice Card */}
        <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-5 sm:p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-sm sm:text-base font-extrabold text-[#261331]">
              Rekomendasi kamu diperbarui dari 12 karya tervalidasi.
            </h2>
            <p className="text-xs text-[#6F607D]">
              Skor adalah peta kecocokan—bukan prediksi masa depan.
            </p>
          </div>
          <span className="px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#ECFDF5] text-[#059669] border border-emerald-200 shrink-0 self-start sm:self-auto">
            Confidence: Strong
          </span>
        </div>

        {/* 2-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Recommendations List (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            {defaultPaths.map((path, idx) => (
              <div
                key={path.rank}
                onClick={() => setSelectedPathIndex(idx)}
                className={`bg-white rounded-[18px] border p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] hover:shadow-[0_8px_24px_rgba(76,29,149,0.12)] transition-all cursor-pointer tal-card-hover ${
                  selectedPathIndex === idx ? 'border-[#8B5CF6] ring-2 ring-purple-100' : 'border-[#E9E1F4]'
                }`}
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <span className="w-8 h-8 rounded-xl bg-[#F3E8FF] text-[#6D28D9] font-black text-sm flex items-center justify-center shrink-0">
                      {path.rank}
                    </span>
                    <div>
                      <h3 className="text-base font-extrabold text-[#261331]">
                        {path.title}
                      </h3>
                      <p className="text-xs text-[#6F607D] mt-0.5">
                        {path.category}
                      </p>
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <span className="text-xl font-black text-[#6D28D9]">
                      {path.match}%
                    </span>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-[#E9E1F4] flex items-center justify-between text-xs">
                  <Link
                    href="/student/portfolio"
                    className="font-bold text-[#6D28D9] hover:text-[#8B5CF6] inline-flex items-center gap-1"
                  >
                    <span>Lihat evidence</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                  <span className="text-[11px] text-[#9584A7]">Provenansi tervalidasi</span>
                </div>
              </div>
            ))}
          </div>

          {/* Right Column: Grounded Rationale Card (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 sm:p-8 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-4">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-purple-100 text-[#6D28D9] flex items-center justify-center">
                  <Sparkles className="w-4 h-4" />
                </div>
                <h3 className="text-base font-extrabold text-[#261331]">
                  Mengapa {currentRationale.title}?
                </h3>
              </div>

              <p className="text-xs text-[#6F607D] leading-relaxed">
                {currentRationale.explanation}
              </p>

              <div className="p-4 rounded-xl bg-[#FCFBFF] border border-[#E9E1F4] space-y-2 text-xs">
                <span className="text-[10px] font-bold text-[#9584A7] uppercase tracking-wider block">
                  Fondasi Penilaian
                </span>
                <p className="font-semibold text-[#261331]">
                  60% Radar Bukti Karya + 20% Tag Keahlian + 20% Rubrik Guru.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-[#FAF5FF] border border-purple-100 text-center">
                <p className="text-[11px] font-semibold text-[#6D28D9]">
                  Rekomendasi bersifat eksploratif dan berbasis bukti nyata.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
