'use client';

import React, { useEffect, useState, useTransition } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';
import { cvService } from '../../../services/cv.service';
import {
  CVBuilderContext,
  CVApprovedPortfolio,
  IssuedCVVersion,
  CVGenerateResponse,
} from '../../../types/cv.types';
import {
  FileCheck2,
  Printer,
  Download,
  QrCode,
  School,
  Award,
  CheckCircle2,
  ExternalLink,
  Sparkles,
  AlertCircle,
  Clock,
  Ban,
  ShieldCheck,
  ChevronRight,
  Layers,
  Copy,
  Check,
} from 'lucide-react';
import Link from 'next/link';

export default function StudentCVPage() {
  const [context, setContext] = useState<CVBuilderContext | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [feedbackMsg, setFeedbackMsg] = useState('');

  // Selection & Form State
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [includeTeacherCompetencies, setIncludeTeacherCompetencies] = useState(true);
  const [includeExploration, setIncludeExploration] = useState(false);

  // Generation UX States: idle | preparing | rendering | issuing | ready
  const [generationStep, setGenerationStep] = useState<'idle' | 'preparing' | 'rendering' | 'issuing' | 'ready'>('idle');
  const [issuanceResult, setIssuanceResult] = useState<CVGenerateResponse | null>(null);
  const [copiedUrl, setCopiedUrl] = useState(false);

  // Downloading state
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [revokingId, setRevokingId] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setErrorMsg('');
    try {
      const data = await cvService.getCVBuilderContext();
      setContext(data);

      // Pre-select up to 4 approved portfolios by default
      if (data.approvedPortfolios && data.approvedPortfolios.length > 0) {
        setSelectedIds(data.approvedPortfolios.slice(0, 4).map((p) => p.portfolioId));
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Gagal memuat data pembuatan CV.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTogglePortfolio = (pid: string) => {
    if (selectedIds.includes(pid)) {
      if (selectedIds.length <= 1) {
        setFeedbackMsg('Pilih minimal 1 karya tervalidasi untuk disertakan dalam CV.');
        return;
      }
      setSelectedIds(selectedIds.filter((id) => id !== pid));
    } else {
      if (selectedIds.length >= (context?.policy?.maxSelectedPortfolios || 8)) {
        setFeedbackMsg(`Maksimal ${context?.policy?.maxSelectedPortfolios || 8} karya yang dapat dipilih.`);
        return;
      }
      setSelectedIds([...selectedIds, pid]);
    }
  };

  const handleGenerateCV = async () => {
    if (selectedIds.length === 0) {
      setErrorMsg('Pilih setidaknya 1 karya tervalidasi.');
      return;
    }

    setErrorMsg('');
    setFeedbackMsg('');
    setGenerationStep('preparing');

    try {
      setTimeout(() => setGenerationStep('rendering'), 400);
      setTimeout(() => setGenerationStep('issuing'), 800);

      const res = await cvService.generateCV({
        portfolioIds: selectedIds,
        includeTeacherCompetencies,
        includeExploration,
      });

      setIssuanceResult(res);
      setGenerationStep('ready');
      setFeedbackMsg(`CV berhasil diterbitkan dengan Kode Dokumen: ${res.displayCode}`);
      // Refresh list of issued versions
      const updatedContext = await cvService.getCVBuilderContext();
      setContext(updatedContext);
    } catch (err: any) {
      setGenerationStep('idle');
      setErrorMsg(err.message || 'Gagal memproses pembuatan CV.');
    }
  };

  const handleDownloadPDF = async (snapshotId: string) => {
    setDownloadingId(snapshotId);
    try {
      const { blob, filename } = await cvService.downloadCVPdf(snapshotId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setErrorMsg(err.message || 'Gagal mengunduh dokumen PDF.');
    } finally {
      setDownloadingId(null);
    }
  };

  const handleRevokeCV = async (snapshotId: string) => {
    if (!window.confirm('Apakah Anda yakin ingin mencabut keabsahan CV ini? Tautan verifikasi publik akan langsung berubah menjadi Tidak Berlaku.')) {
      return;
    }
    setRevokingId(snapshotId);
    try {
      await cvService.revokeCV(snapshotId);
      setFeedbackMsg('Keabsahan CV berhasil dicabut.');
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || 'Gagal mencabut CV.');
    } finally {
      setRevokingId(null);
    }
  };

  const handleCopyVerificationUrl = (url: string) => {
    if (navigator?.clipboard) {
      navigator.clipboard.writeText(url);
      setCopiedUrl(true);
      setTimeout(() => setCopiedUrl(false), 2500);
    }
  };

  const latestVersion = context?.existingVersions?.[0];

  return (
    <AppShell pageTitle="Digital CV & Verifikasi" expectedRole="student">
      <div className="max-w-5xl mx-auto space-y-6 pb-12">
        {/* Header Hero */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 sm:p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                <ShieldCheck className="w-3.5 h-3.5" />
                Standar Verifikasi TALENTRA.ID
              </span>
              {latestVersion && (
                <span className="text-xs text-slate-500 font-mono">Kode: {latestVersion.displayCode}</span>
              )}
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight mt-1.5">
              Penerbitan Digital CV Terverifikasi
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl">
              Diterbitkan dari snapshot karya siswa yang telah disetujui guru. Dilengkapi QR Code autentik dan token berkeamanan tinggi yang dapat diverifikasi publik tanpa membocorkan data pribadi siswa.
            </p>
          </div>

          <div className="flex items-center gap-2.5 shrink-0">
            {latestVersion && latestVersion.status === 'active' && (
              <button
                type="button"
                disabled={downloadingId === latestVersion.snapshotId}
                onClick={() => handleDownloadPDF(latestVersion.snapshotId)}
                className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors shadow-2xs"
              >
                <Download className="w-4 h-4 text-brand-600" />
                <span>{downloadingId === latestVersion.snapshotId ? 'Mengunduh...' : 'Unduh PDF Versi Aktif'}</span>
              </button>
            )}
            <button
              type="button"
              onClick={() => {
                const el = document.getElementById('cv-builder-section');
                el?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold transition-colors shadow-xs"
            >
              <Sparkles className="w-4 h-4" />
              <span>Buat Versi CV Baru</span>
            </button>
          </div>
        </div>

        {/* Notifications */}
        {errorMsg && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs sm:text-sm flex items-start justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
            <button type="button" onClick={() => setErrorMsg('')} className="font-bold text-red-600 hover:text-red-800">
              ✕
            </button>
          </div>
        )}

        {feedbackMsg && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs sm:text-sm flex items-start justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <span>{feedbackMsg}</span>
            </div>
            <button type="button" onClick={() => setFeedbackMsg('')} className="font-bold text-emerald-600 hover:text-emerald-800">
              ✕
            </button>
          </div>
        )}

        {/* Issuance Success Banner with QR Link */}
        {generationStep === 'ready' && issuanceResult && (
          <div className="bg-gradient-to-br from-indigo-900 via-slate-900 to-indigo-950 text-white rounded-2xl p-6 shadow-md border border-indigo-700/50 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-teal-400 bg-teal-950/80 px-2.5 py-1 rounded-md border border-teal-500/30">
                  Dokumen Berhasil Diterbitkan
                </span>
                <h3 className="text-xl font-bold text-white mt-2">
                  CV Terverifikasi Siap Digunakan
                </h3>
                <p className="text-xs text-slate-300 mt-1">
                  Kode Dokumen: <span className="font-mono font-bold text-teal-300">{issuanceResult.displayCode}</span> &bull; Sidik Jari: <span className="font-mono text-slate-300">{issuanceResult.fingerprint}</span>
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={downloadingId === issuanceResult.snapshotId}
                  onClick={() => handleDownloadPDF(issuanceResult.snapshotId)}
                  className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-bold transition-colors shadow-xs"
                >
                  <Download className="w-4 h-4" />
                  <span>{downloadingId === issuanceResult.snapshotId ? 'Mengunduh...' : 'Unduh Berkas PDF'}</span>
                </button>
              </div>
            </div>

            {issuanceResult.verificationUrl && (
              <div className="bg-slate-800/80 p-3.5 rounded-xl border border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <div className="truncate">
                  <span className="text-slate-400 block text-[10px]">Tautan Verifikasi Keaslian Publik:</span>
                  <a
                    href={issuanceResult.verificationUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-teal-300 hover:underline font-mono truncate block"
                  >
                    {issuanceResult.verificationUrl}
                  </a>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => handleCopyVerificationUrl(issuanceResult.verificationUrl!)}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-xs font-medium transition-colors"
                  >
                    {copiedUrl ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedUrl ? 'Tersalin' : 'Salin Tautan'}</span>
                  </button>
                  <Link
                    href={issuanceResult.verificationUrl}
                    target="_blank"
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>Buka Halaman</span>
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}

        {isLoading || !context ? (
          <div className="bg-white p-8 rounded-2xl border border-slate-200">
            <LoadingSkeleton rows={10} />
          </div>
        ) : (
          <>
            {/* Builder Configuration Form */}
            <div id="cv-builder-section" className="bg-white rounded-2xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-6">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <Layers className="w-5 h-5 text-brand-600" />
                  Pilih Karya Portofolio Tervalidasi
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-1">
                  Pilih antara {context.policy.minSelectedPortfolios} hingga {context.policy.maxSelectedPortfolios} karya yang telah disetujui guru untuk ditampilkan dalam dokumen resmi.
                </p>
              </div>

              {context.approvedPortfolios.length === 0 ? (
                <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-300 space-y-2">
                  <Award className="w-8 h-8 text-slate-400 mx-auto" />
                  <p className="text-sm font-semibold text-slate-700">Belum Ada Karya Tervalidasi Guru</p>
                  <p className="text-xs text-slate-500 max-w-md mx-auto">
                    Karya portofolio harus diajukan dan disetujui oleh guru sebelum dapat dimasukkan ke dalam CV resmi.
                  </p>
                  <Link
                    href="/student/portfolio"
                    className="inline-flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 mt-2"
                  >
                    Lihat Status Portofolio Saya &rarr;
                  </Link>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  {context.approvedPortfolios.map((item) => {
                    const isSelected = selectedIds.includes(item.portfolioId);
                    return (
                      <div
                        key={item.portfolioId}
                        onClick={() => handleTogglePortfolio(item.portfolioId)}
                        className={`p-4 rounded-xl border transition-all cursor-pointer select-none flex items-start gap-3 ${
                          isSelected
                            ? 'bg-brand-50/50 border-brand-500 ring-1 ring-brand-500 shadow-2xs'
                            : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}} // Controlled via card click
                          className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 shrink-0 pointer-events-none"
                        />
                        <div className="space-y-1 min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-2">
                            <h4 className="text-xs sm:text-sm font-bold text-slate-900 truncate">{item.title}</h4>
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
                              Disetujui Guru
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-500 capitalize">
                            {item.activityType} &bull; {item.activityDate}
                          </p>
                          <p className="text-xs text-slate-600 line-clamp-2">
                            {item.professionalDescription || item.description}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Additional Options */}
              <div className="pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <label className="flex items-start gap-3 p-3.5 rounded-xl border border-slate-200 hover:bg-slate-50/50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeTeacherCompetencies}
                    onChange={(e) => setIncludeTeacherCompetencies(e.target.checked)}
                    className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 shrink-0"
                  />
                  <div className="text-xs">
                    <span className="font-bold text-slate-800 block">Sertakan Ringkasan Rubrik Kompetensi Guru</span>
                    <span className="text-slate-500">
                      Menampilkan rata-rata dimensi observasi karakter dan keterampilan tanpa memuat identitas guru.
                    </span>
                  </div>
                </label>

                <label className="flex items-start gap-3 p-3.5 rounded-xl border border-slate-200 hover:bg-slate-50/50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeExploration}
                    onChange={(e) => setIncludeExploration(e.target.checked)}
                    className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 shrink-0"
                  />
                  <div className="text-xs">
                    <span className="font-bold text-slate-800 block">Sertakan Bidang Eksplorasi Karier</span>
                    <span className="text-slate-500">
                      Menampilkan minat kluster karier/pendidikan berdasarkan karya tervalidasi (opsional).
                    </span>
                  </div>
                </label>
              </div>

              {/* Generation Action Button */}
              <div className="pt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-slate-100">
                <span className="text-xs text-slate-500">
                  {selectedIds.length} dari {context.policy.maxSelectedPortfolios} karya terpilih.
                </span>

                <button
                  type="button"
                  disabled={generationStep !== 'idle' && generationStep !== 'ready' || selectedIds.length === 0}
                  onClick={handleGenerateCV}
                  className="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-xs font-bold transition-colors shadow-xs"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>
                    {generationStep === 'preparing' && 'Menyiapkan Snapshot...'}
                    {generationStep === 'rendering' && 'Me-render Dokumen PDF...'}
                    {generationStep === 'issuing' && 'Menerbitkan Token QR...'}
                    {(generationStep === 'idle' || generationStep === 'ready') && 'Terbitkan Dokumen CV Resmi'}
                  </span>
                </button>
              </div>
            </div>

            {/* Issued CV Versions History */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-brand-600" />
                    Riwayat Versi CV Terbit
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Setiap versi bersifat permanen (immutable point-in-time document).
                  </p>
                </div>
              </div>

              {context.existingVersions.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">Belum ada versi CV yang pernah diterbitkan.</p>
              ) : (
                <div className="divide-y divide-slate-100">
                  {context.existingVersions.map((v) => (
                    <div key={v.snapshotId} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-slate-900">{v.displayCode}</span>
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full capitalize ${
                              v.status === 'active'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : v.status === 'revoked'
                                ? 'bg-red-50 text-red-700 border border-red-200'
                                : 'bg-slate-100 text-slate-600 border border-slate-200'
                            }`}
                          >
                            {v.status === 'active' ? 'Aktif Terverifikasi' : v.status === 'revoked' ? 'Dicabut' : 'Kedaluwarsa'}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500">
                          Diterbitkan: {new Date(v.issuedAt).toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' })} &bull; {v.selectedProjectCount} Karya Portofolio &bull; Sidik Jari: {v.fingerprint}
                        </p>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          type="button"
                          disabled={downloadingId === v.snapshotId}
                          onClick={() => handleDownloadPDF(v.snapshotId)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-medium text-slate-700 transition-colors"
                        >
                          <Download className="w-3.5 h-3.5 text-brand-600" />
                          <span>{downloadingId === v.snapshotId ? 'Mengunduh...' : 'Unduh PDF'}</span>
                        </button>

                        {v.status === 'active' && (
                          <button
                            type="button"
                            disabled={revokingId === v.snapshotId}
                            onClick={() => handleRevokeCV(v.snapshotId)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-red-200 hover:bg-red-50 text-xs font-medium text-red-600 transition-colors"
                          >
                            <Ban className="w-3.5 h-3.5" />
                            <span>{revokingId === v.snapshotId ? 'Mencabut...' : 'Cabut'}</span>
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
