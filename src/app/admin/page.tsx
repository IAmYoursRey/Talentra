'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '../../components/layout/AppShell';
import { MetricCard } from '../../components/common/MetricCard';
import { TalentHeatmapChart } from '../../components/charts/TalentHeatmapChart';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { ErrorState } from '../../components/common/ErrorState';
import { analyticsService, AnalyticsFilterParams } from '../../services/analytics.service';
import { adminClassService } from '../../services/admin-class.service';
import { authService } from '../../services/auth.service';
import {
  SchoolMetrics,
  TalentHeatmapResponse,
  SchoolRubricAggregate,
  ValidationMetricsResponse,
} from '../../types/analytics.types';
import { AdminClass } from '../../types/admin.types';
import { UserProfile } from '../../types/auth.types';
import {
  Users,
  GraduationCap,
  FileCheck2,
  TrendingUp,
  SlidersHorizontal,
  Clock,
  CheckCircle2,
  RefreshCw,
  School,
  FileEdit,
  XCircle,
  Award,
} from 'lucide-react';
import Link from 'next/link';

export default function AdminDashboardPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [classes, setClasses] = useState<AdminClass[]>([]);

  // Filter state
  const [academicYear, setAcademicYear] = useState('2025/2026');
  const [gradeLevel, setGradeLevel] = useState('all');
  const [classId, setClassId] = useState('all');

  // Analytics data
  const [overviewMetrics, setOverviewMetrics] = useState<SchoolMetrics | null>(null);
  const [talentResponse, setTalentResponse] = useState<TalentHeatmapResponse | null>(null);
  const [rubrics, setRubrics] = useState<SchoolRubricAggregate[]>([]);
  const [rubricsSuppressed, setRubricsSuppressed] = useState(false);
  const [valMetrics, setValMetrics] = useState<ValidationMetricsResponse | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const filters: AnalyticsFilterParams = {
        academicYear: academicYear !== 'all' ? academicYear : undefined,
        gradeLevel: gradeLevel !== 'all' ? gradeLevel : undefined,
        classId: classId !== 'all' ? classId : undefined,
      };

      const [session, classList, m, talent, rub, val] = await Promise.all([
        authService.getCurrentSession(),
        adminClassService.listClasses({ status: 'active' }),
        analyticsService.getSchoolMetrics(),
        analyticsService.getRealTalentHeatmap(filters),
        analyticsService.getSchoolRubrics(filters),
        analyticsService.getValidationMetrics(filters),
      ]);

      setUser(session.user);
      setClasses(classList);
      setOverviewMetrics(m);
      setTalentResponse(talent);
      setRubrics(rub.aggregates);
      setRubricsSuppressed(rub.suppressed);
      setValMetrics(val);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal memuat analitik sekolah.';
      setErrorMsg(msg);
    } finally {
      setIsLoading(false);
    }
  }, [academicYear, gradeLevel, classId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const rubricLabels: Record<string, string> = {
    initiative: 'Inisiatif Mandiri',
    collaboration: 'Kolaborasi Tim',
    communication: 'Komunikasi Kerja',
    responsibility: 'Tanggung Jawab Teknis',
    resilience: 'Resiliensi & Pemecahan Masalah',
  };

  return (
    <AppShell pageTitle="Ekosistem Talenta Sekolah" expectedRole="admin">
      <div className="space-y-6">
        {/* Header Banner */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-intelligence-50 text-intelligence-700 border border-intelligence-200">
                School Talent Intelligence
              </span>
              <span className="text-xs text-slate-400 font-mono">Versi: {talentResponse?.analyticsVersion || 'v1'}</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Ekosistem Talenta & Analitik Sekolah
            </h2>
            <p className="text-sm text-slate-600 max-w-xl leading-relaxed">
              Pemantauan aggregate sebaran talenta siswa, efektivitas validasi guru, dan indikator perkembangan kompetensi kejuruan berbasis karya nyata.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Link
              href="/admin/users"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs transition-colors shadow-2xs"
            >
              <Users className="w-4 h-4" />
              <span>Kelola Pengguna</span>
            </Link>

            <Link
              href="/admin/classes"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-intelligence-600 hover:bg-intelligence-700 text-white font-semibold text-xs transition-colors shadow-xs"
            >
              <School className="w-4 h-4" />
              <span>Manajemen Rombel</span>
            </Link>
          </div>
        </div>

        {/* Operational Metrics Cards (Section 50) */}
        {isLoading || !overviewMetrics ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-white p-5 rounded-2xl border border-slate-200">
                <LoadingSkeleton rows={2} />
              </div>
            ))}
          </div>
        ) : errorMsg ? (
          <ErrorState message={errorMsg} onRetry={loadData} />
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              label="Siswa Aktif"
              value={overviewMetrics.totalActiveStudents}
              subtext="Terdaftar di rombel aktif"
              icon={Users}
              colorScheme="brand"
            />
            <MetricCard
              label="Guru Validator"
              value={overviewMetrics.totalValidators}
              subtext="Pendidik penilai aktif"
              icon={GraduationCap}
              colorScheme="growth"
            />
            <MetricCard
              label="Menunggu Validasi"
              value={overviewMetrics.pendingReviewsCount}
              subtext="Pengajuan dalam antrean"
              icon={FileEdit}
              colorScheme="intelligence"
            />
            <MetricCard
              label="Validasi Selesai"
              value={overviewMetrics.validatedPortfolios}
              subtext={`Tingkat kelulusan ${overviewMetrics.completionRate}%`}
              icon={FileCheck2}
              colorScheme="endorse"
            />
          </div>
        )}

        {/* Cohort / Class Filter Controls (Section 34, 71) */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center gap-2 text-xs text-slate-700 font-semibold">
            <SlidersHorizontal className="w-4 h-4 text-intelligence-600" />
            <span>Filter Analitik Kohor:</span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Academic Year */}
            <select
              value={academicYear}
              onChange={(e) => setAcademicYear(e.target.value)}
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
            >
              <option value="2025/2026">T.A. 2025/2026</option>
              <option value="2024/2025">T.A. 2024/2025</option>
              <option value="all">Semua Tahun</option>
            </select>

            {/* Grade Level */}
            <select
              value={gradeLevel}
              onChange={(e) => setGradeLevel(e.target.value)}
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
            >
              <option value="all">Semua Tingkat</option>
              <option value="10">Kelas 10 (Fase E)</option>
              <option value="11">Kelas 11 (Fase F)</option>
              <option value="12">Kelas 12 (Fase F+)</option>
            </select>

            {/* Class filter */}
            <select
              value={classId}
              onChange={(e) => setClassId(e.target.value)}
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
            >
              <option value="all">Semua Rombel</option>
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>

            <button
              type="button"
              onClick={loadData}
              className="p-1.5 text-slate-500 hover:text-intelligence-600 hover:bg-slate-100 rounded-lg transition-colors"
              title="Perbarui Data"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Two-Column Analytics Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Column 1: School Talent Heatmap (7 cols) */}
          <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-slate-900">Sebaran Cakupan Bukti Talenta (Heatmap)</h3>
                <p className="text-xs text-slate-500">
                  Agregasi 6 dimensi kompetensi kejuruan dari karya siswa tervalidasi
                </p>
              </div>
              <span className="text-[11px] font-bold text-growth-700 bg-growth-50 px-2 py-0.5 rounded border border-growth-200">
                Tervalidasi Guru
              </span>
            </div>

            {isLoading ? (
              <LoadingSkeleton rows={6} />
            ) : (
              <TalentHeatmapChart
                dimensions={talentResponse?.dimensions}
                isCohortSuppressed={talentResponse?.suppressed}
                suppressionReason={talentResponse?.reason}
              />
            )}
          </div>

          {/* Column 2: Teacher Rubric Aggregates & Operational Metrics (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Teacher Rubric Observations */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Observasi Rubrik Guru</h3>
                  <p className="text-xs text-slate-500">Skor rata-rata rubrik sikap & etos kerja (skala 1–5)</p>
                </div>
                <Award className="w-4 h-4 text-intelligence-600" />
              </div>

              {isLoading ? (
                <LoadingSkeleton rows={4} />
              ) : rubricsSuppressed ? (
                <div className="p-4 rounded-xl border border-dashed border-amber-200 bg-amber-50/50 text-center text-xs text-amber-800">
                  Data observasi rubrik disembunyikan untuk menjaga privasi (&ge; 5 siswa tervalidasi).
                </div>
              ) : (
                <div className="space-y-3">
                  {rubrics.map((r) => (
                    <div
                      key={r.dimensionCode}
                      className="p-3 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-between"
                    >
                      <div>
                        <p className="text-xs font-bold text-slate-800">
                          {rubricLabels[r.dimensionCode] || r.dimensionCode}
                        </p>
                        <p className="text-[10px] text-slate-400">
                          {r.assessmentCount} observasi • {r.uniqueStudentCount} siswa
                        </p>
                      </div>

                      <div className="text-right">
                        <span className="text-sm font-bold text-growth-700 font-mono">
                          {r.averageScore ? r.averageScore.toFixed(2) : '-'} / 5.0
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Validation Operations Overview */}
            {valMetrics && (
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">Operasional Validasi</h3>
                    <p className="text-xs text-slate-500">Kinerja peninjauan portofolio sekolah</p>
                  </div>
                  <Clock className="w-4 h-4 text-slate-400" />
                </div>

                <div className="grid grid-cols-2 gap-2.5 text-xs">
                  <div className="p-3 bg-endorse-50/70 border border-endorse-200 rounded-xl">
                    <p className="text-[10px] font-bold text-endorse-800 uppercase">Disetujui (ACC)</p>
                    <p className="text-lg font-bold text-endorse-900 mt-0.5">{valMetrics.approvedCount}</p>
                  </div>

                  <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-xl">
                    <p className="text-[10px] font-bold text-amber-800 uppercase">Perlu Revisi</p>
                    <p className="text-lg font-bold text-amber-900 mt-0.5">{valMetrics.revisionRequestedCount}</p>
                  </div>

                  <div className="p-3 bg-reject-50/70 border border-reject-200 rounded-xl">
                    <p className="text-[10px] font-bold text-reject-800 uppercase">Ditolak</p>
                    <p className="text-lg font-bold text-reject-900 mt-0.5">{valMetrics.rejectedCount}</p>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                    <p className="text-[10px] font-bold text-slate-500 uppercase">Median Turnaround</p>
                    <p className="text-lg font-bold text-slate-800 mt-0.5">{valMetrics.medianTurnaroundHours} Jam</p>
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 flex items-center justify-between">
                  <span>Tingkat Penyelesaian Validasi:</span>
                  <span className="font-bold text-slate-900">{valMetrics.validationCompletionRate}%</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
