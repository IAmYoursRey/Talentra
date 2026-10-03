'use client';

import React, { useEffect, useState } from 'react';
import { AppShell } from '../../components/layout/AppShell';
import { MetricCard } from '../../components/common/MetricCard';
import { SkillRadarChart } from '../../components/charts/SkillRadarChart';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { portfolioService } from '../../services/portfolio.service';
import { skillService } from '../../services/skill.service';
import { authService } from '../../services/auth.service';
import { PortfolioItem } from '../../types/portfolio.types';
import { SkillSnapshot } from '../../types/skill.types';
import { UserProfile } from '../../types/auth.types';
import {
  FolderKanban,
  CheckCircle2,
  Clock,
  Sparkles,
  AlertTriangle,
  ArrowRight,
  PlusCircle,
  TrendingUp,
  Radar,
  Compass,
  FileCheck2,
  ChevronRight,
} from 'lucide-react';
import Link from 'next/link';

export default function StudentDashboardPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [portfolios, setPortfolios] = useState<PortfolioItem[]>([]);
  const [skillSnapshot, setSkillSnapshot] = useState<SkillSnapshot | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      const session = await authService.getCurrentSession();
      setUser(session.user);

      const [items, skills] = await Promise.all([
        portfolioService.getPortfolioItems(),
        skillService.getStudentSkillSnapshot(session.user?.id),
      ]);

      setPortfolios(items);
      setSkillSnapshot(skills);
      setIsLoading(false);
    };

    loadDashboardData();

    const unsubPortfolio = portfolioService.subscribePortfolio(loadDashboardData);
    const unsubSkills = skillService.subscribeSkills(loadDashboardData);

    return () => {
      unsubPortfolio();
      unsubSkills();
    };
  }, []);

  const approvedWorks = portfolios.filter((p) => p.status === 'approved').length || 12;
  const mappedSkills = skillSnapshot?.radarPoints?.filter((s) => s.approvedEvidenceCount > 0).length || 8;
  const cvReadiness = 76;
  const recommendationCount = 4;

  const topCareers = [
    { rank: '01', title: 'Sistem Informasi', match: 92, tag: 'Logika • produk • komunikasi' },
    { rank: '02', title: 'Product / UI Designer', match: 84, tag: 'Desain • presentasi • kreativitas' },
    { rank: '03', title: 'D4 Teknologi Rekayasa', match: 79, tag: 'Build • analisis • problem solving' },
  ];

  return (
    <AppShell pageTitle="Overview" expectedRole="student">
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header matching 02-Student-Overview-HF.svg */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              Selamat pagi, {user?.name.split(' ')[0] || 'Raihan'}
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Jejak karya kamu makin kuat. Lanjutkan momentum minggu ini.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FAF5FF] border border-[#E9E1F4] text-[#A78BFA] font-bold text-xs shadow-xs self-start sm:self-auto">
            <span>Semester 5</span>
          </div>
        </div>

        {/* Mobile Quick Actions matching 22-Mobile-Student-Overview-HF.svg */}
        <div className="md:hidden grid grid-cols-3 gap-3">
          <Link
            href="/student/portfolio/new"
            className="p-3 bg-white rounded-2xl border border-[#E9E1F4] shadow-xs flex flex-col items-center justify-center text-center gap-1.5 active:scale-95 transition-transform"
          >
            <div className="w-8 h-8 rounded-full tal-btn-primary flex items-center justify-center text-white">
              <PlusCircle className="w-4 h-4" />
            </div>
            <span className="text-[11px] font-bold text-[#261331]">Upload</span>
          </Link>

          <Link
            href="/student/skills"
            className="p-3 bg-white rounded-2xl border border-[#E9E1F4] shadow-xs flex flex-col items-center justify-center text-center gap-1.5 active:scale-95 transition-transform"
          >
            <div className="w-8 h-8 rounded-full bg-purple-100 text-[#6D28D9] flex items-center justify-center">
              <Radar className="w-4 h-4" />
            </div>
            <span className="text-[11px] font-bold text-[#261331]">Skill Map</span>
          </Link>

          <Link
            href="/student/career"
            className="p-3 bg-white rounded-2xl border border-[#E9E1F4] shadow-xs flex flex-col items-center justify-center text-center gap-1.5 active:scale-95 transition-transform"
          >
            <div className="w-8 h-8 rounded-full bg-purple-100 text-[#6D28D9] flex items-center justify-center">
              <Compass className="w-4 h-4" />
            </div>
            <span className="text-[11px] font-bold text-[#261331]">Career</span>
          </Link>
        </div>

        {/* 4 Metric Cards Grid matching 02-Student-Overview-HF.svg */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <MetricCard
            indexNumber={1}
            label="Karya tervalidasi"
            value={approvedWorks}
            subtext="+3 semester ini"
            icon={CheckCircle2}
          />
          <MetricCard
            indexNumber={2}
            label="Skill terpetakan"
            value={mappedSkills}
            subtext="6 skill kuat"
            icon={Radar}
          />
          <MetricCard
            indexNumber={3}
            label="Progress CV"
            value={`${cvReadiness}%`}
            subtext="Siap dilengkapi"
            icon={FileCheck2}
          />
          <MetricCard
            indexNumber={4}
            label="Rekomendasi"
            value={recommendationCount}
            subtext="Diperbarui"
            icon={Sparkles}
          />
        </div>

        {/* 2-Column Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Skill Radar & Activity (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {/* Peta Skill Tervalidasi */}
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)]">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-extrabold text-[#261331]">Peta Skill Tervalidasi</h2>
                  <p className="text-xs text-[#6F607D] mt-0.5">
                    Hanya dari karya yang telah di-ACC guru
                  </p>
                </div>
                <Link
                  href="/student/skills"
                  className="text-xs font-bold text-[#6D28D9] hover:text-[#8B5CF6] flex items-center gap-1"
                >
                  <span>Detail</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {isLoading ? (
                <LoadingSkeleton rows={4} />
              ) : (
                <div className="py-2">
                  <SkillRadarChart data={skillSnapshot?.radarPoints || []} height={300} />
                </div>
              )}
            </div>

            {/* Aktivitas Terbaru */}
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)]">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-extrabold text-[#261331]">Aktivitas terbaru</h2>
                  <p className="text-xs text-[#6F607D] mt-0.5">
                    Proof of work yang baru diproses
                  </p>
                </div>
                <Link
                  href="/student/portfolio"
                  className="text-xs font-bold text-[#6D28D9] hover:text-[#8B5CF6] flex items-center gap-1"
                >
                  <span>Lihat semua</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              <div className="space-y-3">
                <div className="p-4 rounded-xl bg-[#FCFBFF] border border-[#E9E1F4] flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <h3 className="text-sm font-bold text-[#261331] truncate">
                      Website Waste2Wisdom
                    </h3>
                    <p className="text-xs text-[#6F607D] mt-0.5">
                      Web Development • 12 Sep 2026
                    </p>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#F7F2FF] text-[#6D28D9] border border-purple-100 shrink-0">
                    Disetujui
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-[#FCFBFF] border border-[#E9E1F4] flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <h3 className="text-sm font-bold text-[#261331] truncate">
                      Presentasi Sejarah Nusantara
                    </h3>
                    <p className="text-xs text-[#6F607D] mt-0.5">
                      Public Speaking • 29 Agu 2026
                    </p>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#FAF5FF] text-[#A78BFA] border border-purple-100 shrink-0">
                    Perlu revisi
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Career Recommendations (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between h-full">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-lg font-extrabold text-[#261331]">Arah Karier & Studi</h2>
                    <p className="text-xs text-[#6F607D] mt-0.5">
                      Rekomendasi dari pola karya + validasi guru
                    </p>
                  </div>
                </div>

                <div className="space-y-3.5 mt-4">
                  {topCareers.map((c) => (
                    <div
                      key={c.rank}
                      className="p-4 rounded-2xl bg-[#FCFBFF] border border-[#E9E1F4] hover:border-purple-300 transition-all space-y-2 tal-card-hover"
                    >
                      <div className="flex items-center justify-between">
                        <span className="w-6 h-6 rounded-full bg-purple-100 text-[#6D28D9] font-extrabold text-xs flex items-center justify-center">
                          {c.rank}
                        </span>
                        <div className="text-right">
                          <span className="text-[10px] text-[#6F607D] font-medium block">
                            Evidence match
                          </span>
                          <span className="text-base font-extrabold text-[#6D28D9]">
                            {c.match}%
                          </span>
                        </div>
                      </div>
                      <h3 className="text-sm font-extrabold text-[#261331]">{c.title}</h3>
                      <p className="text-[11px] text-[#6F607D]">{c.tag}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-6">
                <Link
                  href="/student/career"
                  className="w-full py-3 rounded-xl tal-btn-primary font-bold text-xs flex items-center justify-center gap-2 shadow-md"
                >
                  <span>Eksplorasi Jalur Karier Lengkap</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
