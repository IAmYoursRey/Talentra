'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
  Sparkles,
  Compass,
  CheckCircle2,
  FileCheck2,
  GraduationCap,
  Briefcase,
  HelpCircle,
  AlertTriangle,
  RotateCw,
  Layers,
  Clock,
  Award,
  ChevronRight,
  ShieldCheck,
  Info,
  BookOpen,
} from 'lucide-react';

import { AppShell } from '../../../components/layout/AppShell';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';
import { recommendationService } from '../../../services/recommendation.service';
import {
  RecommendationResponse,
  RecommendationPath,
  RecommendationEvidenceConfidence,
} from '../../../types/recommendation.types';

export default function StudentCareerPage() {
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'career' | 'study'>('all');

  const loadData = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const res = isRefresh
        ? await recommendationService.refreshStudentRecommendations()
        : await recommendationService.getStudentRecommendations();
      setData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Terjadi kesalahan saat memuat rekomendasi eksplorasi.';
      setError(msg);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData(false);
  }, [loadData]);

  const getConfidenceLevelBadge = (level: RecommendationEvidenceConfidence['level']) => {
    switch (level) {
      case 'strong':
        return {
          text: 'Bukti Kuat',
          className: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          desc: 'Didukung oleh banyak bukti portofolio yang konsisten lintas waktu.',
        };
      case 'moderate':
        return {
          text: 'Bukti Cukup',
          className: 'bg-intelligence-50 text-intelligence-700 border-intelligence-200',
          desc: 'Memiliki fondasi bukti terverifikasi yang memadai untuk eksplorasi terarah.',
        };
      case 'developing':
        return {
          text: 'Bukti Berkembang',
          className: 'bg-amber-50 text-amber-700 border-amber-200',
          desc: 'Bukti awal mulai terbentuk; terus tambahkan karya untuk memperjelas pola.',
        };
      case 'limited':
      default:
        return {
          text: 'Bukti Terbatas',
          className: 'bg-slate-100 text-slate-700 border-slate-200',
          desc: 'Data karya tervalidasi masih sedikit; rekomendasi masih bersifat indikasi awal.',
        };
    }
  };

  const hasNoEvidence =
    !data ||
    data.evidenceConfidence.approvedPortfolioCount === 0 ||
    (data.careerPaths.length === 0 && data.studyPaths.length === 0);

  return (
    <AppShell pageTitle="Eksplorasi Studi & Karier" expectedRole="student">
      <div className="space-y-6 max-w-5xl mx-auto px-1 sm:px-0">
        {/* Banner with Intelligence Color */}
        <div className="bg-gradient-to-r from-intelligence-900 via-slate-900 to-brand-950 rounded-2xl p-6 sm:p-8 text-white shadow-xs space-y-4 relative overflow-hidden">
          <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-intelligence-500/10 blur-3xl pointer-events-none" />

          <div className="relative z-10 flex flex-wrap items-center justify-between gap-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-intelligence-500/30 text-intelligence-200 border border-intelligence-400/30">
              <Sparkles className="w-3.5 h-3.5 text-intelligence-300" />
              <span>Evidence-Based Career & Study Engine</span>
            </span>

            {data && (
              <button
                onClick={() => loadData(true)}
                disabled={isRefreshing || isLoading}
                className="inline-flex items-center gap-1.5 text-xs text-slate-300 bg-white/10 hover:bg-white/20 border border-white/15 px-3 py-1.5 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
                title="Perbarui rekomendasi dengan karya terbaru"
              >
                <RotateCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
                <span>{isRefreshing ? 'Memperbarui...' : 'Perbarui Analisis'}</span>
              </button>
            )}
          </div>

          <div className="relative z-10 space-y-1.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Bidang yang Dapat Kamu Eksplorasi
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
              Rekomendasi di bawah disusun secara transparan dan deterministik dari karya portofolio yang telah
              disetujui guru pembimbing dan observasi rubrik sekolah.
            </p>
          </div>

          <div className="relative z-10 pt-1 text-[11px] text-slate-400 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-intelligence-400 shrink-0" />
            <span>
              Panduan eksploratif: Bukan penentu kelulusan, seleksi penerimaan perguruan tinggi, atau prediksi karier mutlak.
            </span>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="space-y-4">
            <LoadingSkeleton rows={4} />
            <LoadingSkeleton rows={4} />
          </div>
        )}

        {/* Error State */}
        {!isLoading && error && (
          <div className="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-rose-800 space-y-3">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-rose-900">Gagal Memuat Rekomendasi</h3>
                <p className="text-xs text-rose-700">{error}</p>
              </div>
            </div>
            <button
              onClick={() => loadData(false)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition cursor-pointer"
            >
              <RotateCw className="w-3.5 h-3.5" />
              <span>Coba Lagi</span>
            </button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && hasNoEvidence && (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-8 sm:p-12 text-center space-y-4 shadow-xs">
            <div className="w-14 h-14 bg-intelligence-50 text-intelligence-600 rounded-2xl flex items-center justify-center mx-auto border border-intelligence-100">
              <Compass className="w-7 h-7" />
            </div>
            <div className="max-w-md mx-auto space-y-2">
              <h3 className="text-base sm:text-lg font-bold text-slate-900">
                Belum Cukup Bukti Tervalidasi
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                TALENTRA memerlukan portofolio karya yang telah disetujui guru pembimbing sekolah untuk membentuk
                rekomendasi eksplorasi karier dan program studi yang akurat.
              </p>
            </div>
            <div className="pt-2">
              <Link
                href="/student/portfolio"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-intelligence-600 text-white text-xs font-semibold hover:bg-intelligence-700 transition shadow-xs"
              >
                <span>Mulai Tambahkan Karya</span>
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        )}

        {/* Main Content when Evidence is Available */}
        {!isLoading && !error && data && !hasNoEvidence && (
          <div className="space-y-6">
            {/* Evidence Confidence Card */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-intelligence-600" />
                      <span>Tingkat Ketercukupan Bukti (Evidence Sufficiency)</span>
                    </h2>
                  </div>
                  <p className="text-xs text-slate-500">
                    Mengukur seberapa kaya dan konsisten bukti karya portofolio yang mendasari analisis ini.
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold border ${
                      getConfidenceLevelBadge(data.evidenceConfidence.level).className
                    }`}
                  >
                    {getConfidenceLevelBadge(data.evidenceConfidence.level).text}
                  </span>
                  <span className="text-xs font-mono font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                    Skor: {data.evidenceConfidence.score}/100
                  </span>
                </div>
              </div>

              {/* Confidence Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <p className="text-[11px] font-semibold text-slate-500 flex items-center gap-1.5">
                    <FileCheck2 className="w-3.5 h-3.5 text-brand-600" />
                    <span>Karya Tervalidasi</span>
                  </p>
                  <p className="text-lg font-bold text-slate-900 mt-1">
                    {data.evidenceConfidence.approvedPortfolioCount} Karya
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <p className="text-[11px] font-semibold text-slate-500 flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-intelligence-600" />
                    <span>Keragaman Dimensi</span>
                  </p>
                  <p className="text-lg font-bold text-slate-900 mt-1">
                    {data.evidenceConfidence.distinctDimensionCount} dari 6
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <p className="text-[11px] font-semibold text-slate-500 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-growth-600" />
                    <span>Rentang Waktu</span>
                  </p>
                  <p className="text-lg font-bold text-slate-900 mt-1">
                    {data.evidenceConfidence.timeSpanMonths} Bulan
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <p className="text-[11px] font-semibold text-slate-500 flex items-center gap-1.5">
                    <Award className="w-3.5 h-3.5 text-amber-600" />
                    <span>Observasi Rubrik</span>
                  </p>
                  <p className="text-lg font-bold text-slate-900 mt-1">
                    {data.evidenceConfidence.rubricAssessmentCount} Penilaian
                  </p>
                </div>
              </div>

              <div className="text-[11px] text-slate-500 bg-intelligence-50/40 p-3 rounded-xl border border-intelligence-100 leading-relaxed">
                <strong>Catatan Prinsip:</strong> Tingkat ketercukupan bukti menunjukkan seberapa banyak dan konsisten
                rekam jejak portofolio yang terkumpul — <em>bukan probabilitas keberhasilan karier atau kecerdasan siswa</em>.
              </div>
            </div>

            {/* Navigation Filter Tabs */}
            <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                  activeTab === 'all'
                    ? 'bg-slate-900 text-white'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Semua Bidang ({data.careerPaths.length + data.studyPaths.length})
              </button>
              <button
                onClick={() => setActiveTab('career')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
                  activeTab === 'career'
                    ? 'bg-intelligence-600 text-white'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Briefcase className="w-3.5 h-3.5" />
                <span>Bidang Karier ({data.careerPaths.length})</span>
              </button>
              <button
                onClick={() => setActiveTab('study')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
                  activeTab === 'study'
                    ? 'bg-brand-600 text-white'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <GraduationCap className="w-3.5 h-3.5" />
                <span>Program Studi ({data.studyPaths.length})</span>
              </button>
            </div>

            {/* Career Exploration Paths Section */}
            {(activeTab === 'all' || activeTab === 'career') && data.careerPaths.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <Briefcase className="w-5 h-5 text-intelligence-600" />
                    <span>Bidang Karier untuk Dieksplorasi</span>
                  </h2>
                  <span className="text-xs text-slate-500 font-medium">Berdasarkan kesesuaian bukti karya</span>
                </div>

                <div className="space-y-4">
                  {data.careerPaths.map((path, idx) => (
                    <RecommendationCard key={path.id || path.code} path={path} index={idx} type="career" />
                  ))}
                </div>
              </div>
            )}

            {/* Study Exploration Paths Section */}
            {(activeTab === 'all' || activeTab === 'study') && data.studyPaths.length > 0 && (
              <div className="space-y-4 pt-2">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <GraduationCap className="w-5 h-5 text-brand-600" />
                    <span>Program Studi Pendidikan Tinggi untuk Dieksplorasi</span>
                  </h2>
                  <span className="text-xs text-slate-500 font-medium">Rujukan studi lanjut relevan</span>
                </div>

                <div className="space-y-4">
                  {data.studyPaths.map((path, idx) => (
                    <RecommendationCard key={path.id || path.code} path={path} index={idx} type="study" />
                  ))}
                </div>
              </div>
            )}

            {/* How TALENTRA Calculates This Card */}
            <div className="bg-slate-50 rounded-2xl border border-slate-200/80 p-6 space-y-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-slate-700" />
                <span>Bagaimana TALENTRA Menghitung Rekomendasi Ini?</span>
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                TALENTRA menggunakan karya portofolio yang telah disetujui guru, tag kemampuan kanonikal, pola bukti
                dari waktu ke waktu, dan observasi rubrik guru. Rekomendasi ini merupakan alat eksplorasi mandiri
                dan dapat terus berkembang seiring bertambahnya karya tervalidasi.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 text-[11px] text-slate-600">
                <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                  <strong className="text-slate-800 block mb-0.5">1. Bukti Radar (60%)</strong>
                  Kesesuaian 6 dimensi kompetensi siswa terhadap profil bidang.
                </div>
                <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                  <strong className="text-slate-800 block mb-0.5">2. Tag Spesifik (20%)</strong>
                  Karya tervalidasi dengan tag spesifik yang selaras dengan bidang.
                </div>
                <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                  <strong className="text-slate-800 block mb-0.5">3. Observasi Guru (20%)</strong>
                  Penilaian rubrik soft-skill guru (disesuaikan jika belum tersedia).
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

function RecommendationCard({
  path,
  index,
  type,
}: {
  path: RecommendationPath;
  index: number;
  type: 'career' | 'study';
}) {
  const isCareer = type === 'career';
  const badgeColor = isCareer
    ? 'text-intelligence-700 bg-intelligence-50 border-intelligence-200'
    : 'text-brand-700 bg-brand-50 border-brand-200';

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-5 sm:p-7 shadow-xs hover:border-intelligence-300 transition-all space-y-5">
      {/* Top Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${badgeColor}`}>
              Opsi #{index + 1}
            </span>
            <span className="text-xs text-slate-400 font-medium">• {path.cluster}</span>
          </div>
          <h3 className="text-lg sm:text-xl font-bold text-slate-900 leading-snug">{path.title}</h3>
          <p className="text-xs text-slate-600 max-w-2xl">{path.description}</p>
        </div>

        {/* Match Metric */}
        <div className="self-start sm:self-center shrink-0 text-left sm:text-right bg-slate-50 sm:bg-transparent p-3 sm:p-0 rounded-xl sm:rounded-none w-full sm:w-auto">
          <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Kesesuaian Bukti</p>
          <div className="flex items-baseline gap-1.5 sm:justify-end">
            <span className="text-2xl font-extrabold text-intelligence-600">{path.matchScore}%</span>
            <span className="text-xs text-slate-500 font-medium">Relevan</span>
          </div>
          {/* Component Mini Breakdown */}
          <p className="text-[10px] text-slate-400">
            Radar {path.components.radarMatch}% • Tag {path.components.tagMatch}% • Rubrik {path.components.rubricMatch}%
          </p>
        </div>
      </div>

      {/* Supporting Dimensions & Supporting Portfolios Provenance */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Supporting Competency Dimensions */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
          <p className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-growth-600" />
            <span>Dimensi Kompetensi Pendukung:</span>
          </p>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {path.supportingDimensions.length > 0 ? (
              path.supportingDimensions.map((dim) => (
                <span
                  key={dim.dimension}
                  className="px-2.5 py-1 rounded-lg text-xs font-medium bg-white border border-slate-200 text-slate-700 shadow-2xs"
                >
                  {dim.dimension}: {dim.score}%
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-400 italic">Belum ada dimensi spesifik</span>
            )}
          </div>

          {/* Supporting Tags */}
          {path.supportingTags && path.supportingTags.length > 0 && (
            <div className="pt-2 border-t border-slate-200/60 mt-2">
              <p className="text-[11px] font-semibold text-slate-500 mb-1">Tag Portofolio Selaras:</p>
              <div className="flex flex-wrap gap-1">
                {path.supportingTags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 rounded text-[11px] bg-slate-200/70 text-slate-700 font-mono"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Grounded Evidence Provenance */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
          <p className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <FileCheck2 className="w-4 h-4 text-brand-600" />
            <span>{path.evidenceCount} Karya Tervalidasi yang Mendasari:</span>
          </p>
          {path.supportingPortfolios && path.supportingPortfolios.length > 0 ? (
            <ul className="text-xs text-slate-700 space-y-1.5 list-none">
              {path.supportingPortfolios.slice(0, 4).map((p, i) => (
                <li key={i} className="flex items-center gap-1.5 truncate">
                  <span className="w-1.5 h-1.5 rounded-full bg-intelligence-500 shrink-0" />
                  <span className="font-semibold text-slate-800 truncate">{p.title}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-500 italic">
              Didukung oleh pola umum kompetensi radar yang telah terverifikasi.
            </p>
          )}
        </div>
      </div>

      {/* Rationale Explanation */}
      <div className="p-4 rounded-xl bg-intelligence-50/50 border border-intelligence-200/80 space-y-1.5">
        <p className="text-xs font-bold text-intelligence-900 flex items-center gap-1.5">
          <HelpCircle className="w-4 h-4 text-intelligence-600" />
          <span>Mengapa Bidang Ini Direkomendasikan?</span>
        </p>
        <p className="text-xs text-slate-700 leading-relaxed">{path.rationale}</p>
      </div>

      {/* Suggested Pathways */}
      {path.suggestedPathways && path.suggestedPathways.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            Jalur Eksplorasi Relevan:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {path.suggestedPathways.map((pw, pIdx) => (
              <div
                key={pIdx}
                className="p-2.5 rounded-lg border border-slate-200 bg-white text-xs text-slate-700 flex items-start gap-2"
              >
                {isCareer ? (
                  <Briefcase className="w-3.5 h-3.5 text-growth-600 shrink-0 mt-0.5" />
                ) : (
                  <GraduationCap className="w-3.5 h-3.5 text-brand-600 shrink-0 mt-0.5" />
                )}
                <span className="leading-tight">{pw}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
