'use client';

import React, { useEffect, useState } from 'react';
import { AppShell } from '../../components/layout/AppShell';
import { MetricCard } from '../../components/common/MetricCard';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { analyticsService } from '../../services/analytics.service';
import { authService } from '../../services/auth.service';
import {
  Users,
  GraduationCap,
  FileCheck2,
  TrendingUp,
  School,
  Sparkles,
  ChevronRight,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import Link from 'next/link';

export default function AdminDashboardPage() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    analyticsService
      .getSchoolMetrics()
      .catch(() => null)
      .finally(() => setIsLoading(false));
  }, []);

  const topDomains = [
    { name: 'Technology & Coding', percentage: 72 },
    { name: 'Communication', percentage: 61 },
    { name: 'Leadership', percentage: 48 },
    { name: 'Creative & Design', percentage: 43 },
    { name: 'Science & Analysis', percentage: 37 },
  ];

  const rombelSnapshots = [
    { name: 'X IPA 1', coverage: 86 },
    { name: 'XI IPA 2', coverage: 74 },
    { name: 'XII IPA 1', coverage: 91 },
    { name: 'XII IPS 2', coverage: 68 },
  ];

  return (
    <AppShell pageTitle="Overview" expectedRole="admin" isPageLoading={isLoading}>
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header matching 17-Admin-Overview-HF.svg */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              School Talent Overview
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Ringkasan tren bakat sekolah dalam bentuk agregat.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#F3E8FF] border border-purple-200 text-[#6D28D9] font-bold text-xs shadow-xs self-start sm:self-auto">
            <span>2026 • Semester 1</span>
          </div>
        </div>

        {/* 4 Metric Cards Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <MetricCard
            indexNumber={1}
            label="Siswa aktif"
            value="842"
            subtext="+6.2%"
            icon={GraduationCap}
            href="/admin/users"
          />
          <MetricCard
            indexNumber={2}
            label="Karya tervalidasi"
            value="2,481"
            subtext="+184"
            icon={CheckCircle2}
            href="/admin/heatmap"
          />
          <MetricCard
            indexNumber={3}
            label="Guru validator"
            value="54"
            subtext="92% aktif"
            icon={Users}
            href="/admin/users"
          />
          <MetricCard
            indexNumber={4}
            label="CV terbit"
            value="316"
            subtext="+31 bulan ini"
            icon={FileCheck2}
            href="/admin/classes"
          />
        </div>

        {/* 2-Column Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Talent Heatmap Sekolah (7 cols) */}
          <div className="lg:col-span-7 bg-white rounded-[18px] border border-[#E9E1F4] p-6 sm:p-8 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between space-y-6">
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-extrabold text-[#261331]">
                    Talent Heatmap Sekolah
                  </h2>
                  <p className="text-xs text-[#6F607D] mt-0.5">
                    Persentase siswa dengan evidence tervalidasi
                  </p>
                </div>
                <Link
                  href="/admin/heatmap"
                  className="text-xs font-bold text-[#6D28D9] hover:text-[#8B5CF6] flex items-center gap-1"
                >
                  <span>Lihat Heatmap</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              <div className="space-y-4">
                {topDomains.map((dom) => (
                  <div key={dom.name} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[#261331]">{dom.name}</span>
                      <span className="font-extrabold text-[#6D28D9]">{dom.percentage}%</span>
                    </div>
                    <div className="w-full h-2.5 rounded-full bg-[#F3E8FF] overflow-hidden">
                      <div
                        className="h-full rounded-full tal-btn-primary transition-all duration-500"
                        style={{ width: `${dom.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-[#F3E8FF] border border-purple-200 flex items-center gap-2.5">
              <Sparkles className="w-4 h-4 text-[#6D28D9] shrink-0" />
              <p className="text-xs font-bold text-[#6D28D9]">
                Insight: teknologi tumbuh paling cepat pada kelas XII.
              </p>
            </div>
          </div>

          {/* Right Column: Rombel Snapshot & Management (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Rombel Snapshot Card */}
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-extrabold text-[#261331]">Rombel snapshot</h3>
                  <p className="text-xs text-[#6F607D] mt-0.5">Distribusi karya tervalidasi</p>
                </div>
              </div>

              <div className="space-y-2.5">
                {rombelSnapshots.map((r) => (
                  <div
                    key={r.name}
                    className="p-3 rounded-xl bg-[#FCFBFF] border border-[#E9E1F4] flex items-center justify-between text-xs"
                  >
                    <span className="font-bold text-[#261331]">{r.name}</span>
                    <span className="px-2.5 py-0.5 rounded-full font-extrabold text-[11px] bg-[#F7F2FF] text-[#6D28D9]">
                      {r.coverage}%
                    </span>
                  </div>
                ))}
              </div>

              <div className="pt-2 text-center">
                <span className="text-[11px] text-[#9584A7] font-semibold">
                  Agregat saja • cohort ≥ 5
                </span>
              </div>
            </div>

            {/* User & Class Management Card */}
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-4">
              <div>
                <h3 className="text-base font-extrabold text-[#261331]">
                  User & Class Management
                </h3>
                <p className="text-xs text-[#6F607D] mt-0.5">
                  Kelola akun, rombel, assignment validator, dan reset password.
                </p>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center py-2">
                <div className="p-3 rounded-xl bg-[#FCFBFF] border border-[#E9E1F4]">
                  <p className="text-lg font-black text-[#261331]">842</p>
                  <p className="text-[10px] text-[#6F607D] font-bold">Siswa</p>
                </div>
                <div className="p-3 rounded-xl bg-[#FCFBFF] border border-[#E9E1F4]">
                  <p className="text-lg font-black text-[#261331]">54</p>
                  <p className="text-[10px] text-[#6F607D] font-bold">Guru</p>
                </div>
                <div className="p-3 rounded-xl bg-[#FCFBFF] border border-[#E9E1F4]">
                  <p className="text-lg font-black text-[#261331]">27</p>
                  <p className="text-[10px] text-[#6F607D] font-bold">Kelas</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2">
                <Link
                  href="/admin/users"
                  className="py-2.5 rounded-xl tal-btn-primary font-bold text-xs text-center"
                >
                  Kelola Users
                </Link>
                <Link
                  href="/admin/classes"
                  className="py-2.5 rounded-xl tal-btn-secondary font-bold text-xs text-center"
                >
                  Kelola Kelas
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
