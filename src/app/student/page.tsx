'use client';

import React, { useEffect, useState } from 'react';
import { AppShell } from '../../components/layout/AppShell';
import { MetricCard } from '../../components/common/MetricCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { TagChip } from '../../components/common/TagChip';
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
  FileCheck,
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

  const totalWorks = portfolios.length;
  const approvedWorks = portfolios.filter((p) => p.status === 'approved').length;
  const pendingWorks = portfolios.filter((p) => p.status === 'submitted').length;
  const revisionItems = portfolios.filter((p) => p.status === 'revision_requested');
  const recentPortfolios = portfolios.slice(0, 4);

  // CV readiness score estimate based on approved works
  const cvReadiness = Math.min(100, Math.round((approvedWorks / 3) * 100));

  return (
    <AppShell pageTitle="Beranda Siswa" expectedRole="student">
      <div className="space-y-6">
        {/* Welcome Greeting & Action Banner */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200">
                Portofolio Aktif
              </span>
              <span className="text-xs text-slate-400">• {user?.className || 'XII RPL 1'}</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Selamat datang, {user?.name.split(' ')[0] || 'Alya'} 👋
            </h2>
            <p className="text-sm text-slate-600 max-w-xl leading-relaxed">
              Pantau perkembangan portofolio karya nyata Anda, respons catatan revisi guru pembimbing, dan bangun rekam jejak kompetensi digital.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Link
              href="/student/portfolio/new"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-sm transition-all shadow-xs hover:shadow-sm focus:ring-2 focus:ring-brand-500"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Tambah Karya Baru</span>
            </Link>
          </div>
        </div>

        {/* Action Needed Card: Revision Requested */}
        {revisionItems.length > 0 && (
          <div className="p-4 sm:p-5 rounded-2xl border border-revision-300 bg-revision-50/70 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-revision-100 text-revision-700 flex items-center justify-center shrink-0 border border-revision-200">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-revision-900">Perlu Tindak Lanjut: Catatan Revisi Guru</h3>
                  <span className="text-[11px] font-bold px-1.5 py-0.5 rounded bg-revision-200/80 text-revision-800">
                    {revisionItems.length} Karya
                  </span>
                </div>
                <p className="text-xs text-revision-800 mt-1 line-clamp-2 max-w-2xl leading-relaxed">
                  Guru pembimbing telah memberikan catatan revisi pada <strong>&ldquo;{revisionItems[0].title}&rdquo;</strong>:{' '}
                  &ldquo;{revisionItems[0].teacherFeedback || 'Mohon lengkapi berkas bukti karya.'}&rdquo;
                </p>
              </div>
            </div>
            <Link
              href={`/student/portfolio/${revisionItems[0].id}`}
              className="inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-lg bg-revision-500 hover:bg-revision-600 text-white font-semibold text-xs transition-colors shrink-0 shadow-xs"
            >
              <span>Perbaiki Sekarang</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        )}

        {/* Metrics Row */}
        {isLoading ? (
          <LoadingSkeleton rows={2} />
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              label="Total Karya"
              value={totalWorks}
              subtext="Karya terdaftar di akun"
              icon={FolderKanban}
              colorScheme="brand"
            />
            <MetricCard
              label="Karya Disetujui"
              value={approvedWorks}
              subtext="Tervalidasi pembimbing"
              icon={CheckCircle2}
              colorScheme="endorse"
              badge="Aktif"
            />
            <MetricCard
              label="Menunggu Validasi"
              value={pendingWorks}
              subtext="Dalam antrean guru"
              icon={Clock}
              colorScheme="revision"
            />
            <MetricCard
              label="Kesiapan CV Digital"
              value={`${cvReadiness}%`}
              subtext="Berdasarkan bukti resmi"
              icon={FileCheck}
              colorScheme="growth"
              badge={cvReadiness >= 100 ? 'Lengkap' : 'Dalam Proses'}
            />
          </div>
        )}

        {/* Two-Column Layout: Skill Snapshot & Career Preview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Radar Chart Snapshot */}
          <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-growth-50 text-growth-700 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Skill Snapshot</h3>
                  <p className="text-xs text-slate-500">
                    Kalkulasi kompetensi dari {approvedWorks} karya yang telah disetujui guru
                  </p>
                </div>
              </div>
              <Link
                href="/student/skills"
                className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1"
              >
                <span>Lihat Detail</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {isLoading ? (
              <LoadingSkeleton rows={4} />
            ) : (
              <SkillRadarChart
                data={skillSnapshot?.radarPoints || []}
                height={280}
                showTextAlternative={false}
              />
            )}
          </div>

          {/* Career Insight Preview Card */}
          <div className="bg-gradient-to-br from-white to-intelligence-50/40 rounded-2xl border border-intelligence-200/80 p-6 shadow-xs flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-intelligence-50 text-intelligence-700 border border-intelligence-200">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Eksplorasi Studi & Karier</span>
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Demo Preview</span>
              </div>

              <div>
                <h4 className="text-base font-bold text-slate-900 leading-snug">
                  Potensi Kuat pada Digital Product & Communication
                </h4>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  Berdasarkan bukti karya tervalidasi yang menunjukkan konsistensi pada pengembangan produk web dan komunikasi publik.
                </p>
              </div>

              <div className="p-3 bg-white rounded-xl border border-intelligence-100 shadow-2xs space-y-2">
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  Bidang yang Dapat Dieksplorasi:
                </p>
                <div className="flex flex-wrap gap-1.5">
                  <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-intelligence-50 text-intelligence-800">
                    Sistem Informasi
                  </span>
                  <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-brand-50 text-brand-800">
                    UI/UX Design
                  </span>
                  <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-growth-50 text-growth-800">
                    Digital Business
                  </span>
                </div>
              </div>
            </div>

            <Link
              href="/student/career"
              className="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-intelligence-600 hover:bg-intelligence-700 text-white font-semibold text-xs transition-colors shadow-xs"
            >
              <span>Buka Analisis Rekomendasi</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Recent Portfolios Section */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Karya Terbaru</h3>
              <p className="text-xs text-slate-500">Daftar unggahan karya dan status validasi terkini</p>
            </div>
            <Link
              href="/student/portfolio"
              className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1"
            >
              <span>Lihat Semua ({totalWorks})</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="divide-y divide-slate-100">
            {recentPortfolios.map((item) => (
              <div
                key={item.id}
                className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/60 px-2 rounded-xl transition-colors"
              >
                <div className="space-y-1.5 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <StatusBadge status={item.status} size="sm" />
                    <span className="text-xs text-slate-400">• {item.date}</span>
                    <span className="text-xs text-slate-500 capitalize bg-slate-100 px-2 py-0.5 rounded">
                      {item.activityType}
                    </span>
                  </div>
                  <Link
                    href={`/student/portfolio/${item.id}`}
                    className="text-sm font-bold text-slate-900 hover:text-brand-600 truncate block"
                  >
                    {item.title}
                  </Link>
                  <div className="flex flex-wrap gap-1">
                    {item.tags.map((t) => (
                      <TagChip key={t} label={t} size="sm" />
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-2 self-start sm:self-center shrink-0">
                  <Link
                    href={`/student/portfolio/${item.id}`}
                    className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-xs font-medium text-slate-700 transition-colors"
                  >
                    Detail
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
