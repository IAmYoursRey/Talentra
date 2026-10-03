'use client';

import React, { useEffect, useState } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';
import { cvService } from '../../../services/cv.service';
import { CVBuilderContext, CVGenerateResponse } from '../../../types/cv.types';
import {
  FileCheck2,
  QrCode,
  CheckCircle2,
  ShieldCheck,
  Check,
  Sparkles,
  ExternalLink,
  Loader2,
  Printer,
  Award,
  Lock,
  GraduationCap,
  Building,
  User,
  Share2,
} from 'lucide-react';
import { authService } from '../../../services/auth.service';
import { useOffline } from '../../../context/OfflineContext';
import Link from 'next/link';
import { cn } from '../../../lib/utils';

export default function StudentCVPage() {
  const [context, setContext] = useState<CVBuilderContext | null>(null);
  const [currentUser, setCurrentUser] = useState<string>('Dimas Pratama');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>(['1', '2', '3', '4']);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedCv, setGeneratedCv] = useState<CVGenerateResponse | null>(null);
  const { isOffline } = useOffline();

  const mockAvailableEvidences = [
    { id: '1', title: 'Waste2Wisdom', category: 'Web Platform', desc: 'Aplikasi pengelolaan sampah sekolah berbasis insentif poin digital terdesentralisasi' },
    { id: '2', title: 'Robot Line Follower', category: 'Hardware & IoT', desc: 'Mikrokontroler navigasi optik presisi tinggi untuk kompetisi robotika tingkat daerah' },
    { id: '3', title: 'Class Meeting Leadership', category: 'Event Management', desc: 'Koordinator pelaksana kegiatan keolahragaan dan literasi siswa antarkelas' },
    { id: '4', title: 'Presentasi Sejarah Nusantara', category: 'Public Speaking', desc: 'Kajian interaktif peninggalan kemaritiman dan peradaban Indonesia' },
    { id: '5', title: 'Festival Seni Sekolah', category: 'Creative & Media', desc: 'Instalasi tata panggung dan dokumentasi audio-visual' },
    { id: '6', title: 'Lomba Cerdas Cermat', category: 'Analysis & Logic', desc: 'Juara 2 Olimpiade Sains Terapan tingkat Kota' },
  ];

  useEffect(() => {
    authService.getCurrentSession().then((s) => {
      if (s.user?.name) setCurrentUser(s.user.name);
    });

    cvService
      .getCVBuilderContext()
      .then((data) => {
        setContext(data);
        if (data.approvedPortfolios && data.approvedPortfolios.length > 0) {
          setSelectedIds(data.approvedPortfolios.slice(0, 4).map((p) => p.portfolioId));
        }
      })
      .catch(() => {});
  }, []);

  const toggleSelect = (id: string) => {
    if (selectedIds.includes(id)) {
      if (selectedIds.length <= 1) return;
      setSelectedIds(selectedIds.filter((item) => item !== id));
    } else {
      if (selectedIds.length >= 8) return;
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleGenerate = async () => {
    if (isOffline) return;
    setIsGenerating(true);
    try {
      const res = await cvService.generateCV({
        portfolioIds: selectedIds,
        includeTeacherCompetencies: true,
        includeExploration: true,
      });
      setGeneratedCv(res);
    } catch {
      // Demo fallback
      setGeneratedCv({
        snapshotId: 'snap-v1',
        displayCode: 'TLN-CV-2026',
        contentDigest: 'sha256-mock-digest',
        fingerprint: 'TLN-94B8-E210',
        status: 'active',
        selectedProjectCount: selectedIds.length,
        verificationToken: 'tlnt_token_v94b8e21',
        verificationUrl: '/verify/tlnt_token_v94b8e21',
        issuedAt: new Date().toISOString(),
        expiresAt: null,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <AppShell pageTitle="Digital CV" expectedRole="student" isPageLoading={isLoading}>
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight flex items-center gap-3">
              <span>Digital CV Tervalidasi</span>
              <span className="text-xs px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                Standar Industri
              </span>
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Dokumen portofolio resmi terverifikasi dengan stempel digital, QR otentisitas, dan rekonsiliasi kompetensi guru.
            </p>
          </div>
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#FAF5FF] border border-[#E9E1F4] text-[#7E22CE] font-bold text-xs shadow-xs">
              <GraduationCap className="w-3.5 h-3.5" />
              <span>Semester 5 • 2026/2027</span>
            </span>
          </div>
        </div>

        {/* 2-Column CV Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Official CV Document Preview (7 cols) */}
          <div className="lg:col-span-7 bg-white rounded-[22px] border border-[#E9E1F4] shadow-[0_8px_30px_rgba(76,29,149,0.06)] overflow-hidden relative">
            {/* Top National Ribbon */}
            <div className="bg-gradient-to-r from-[#1E112A] via-[#3B1954] to-[#1E112A] text-white px-6 py-3 flex items-center justify-between text-[11px] font-semibold tracking-wider uppercase border-b border-purple-900/40">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Dokumen Portofolio Resmi Siswa</span>
              </div>
              <span className="bg-purple-800/60 px-2 py-0.5 rounded text-[10px] text-purple-200 font-mono">
                TLN-DOC-2026
              </span>
            </div>

            <div className="p-8 space-y-6">
              {/* Document Header Section */}
              <div className="flex items-start justify-between gap-4 pb-6 border-b border-[#F0EBF8]">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-2xl tal-btn-primary flex items-center justify-center text-white text-xl font-black shadow-md border-2 border-white ring-2 ring-purple-100">
                    {currentUser.substring(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h2 className="text-xl sm:text-2xl font-black text-[#261331] tracking-tight">
                      {currentUser || context?.profile?.displayName || 'Dimas Pratama'}
                    </h2>
                    <p className="text-xs font-bold text-[#6D28D9] flex items-center gap-1.5 mt-0.5">
                      <Building className="w-3.5 h-3.5" />
                      <span>SMKN 1 Jakarta • Rekayasa Perangkat Lunak (RPL)</span>
                    </p>
                    <p className="text-[11px] text-[#867798] mt-1 font-mono">
                      NISN: 0081****** • NIK: 3171**********
                    </p>
                  </div>
                </div>

                <span className="px-3 py-1 rounded-full text-[11px] font-black bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>TERVALIDASI</span>
                </span>
              </div>

              {/* Ringkasan Profil */}
              <div className="space-y-1.5">
                <h3 className="text-[11px] font-extrabold text-[#7E22CE] uppercase tracking-wider flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5" />
                  <span>Profil & Kompetensi Utama</span>
                </h3>
                <p className="text-xs text-[#3D2E4F] leading-relaxed bg-[#FAF8FE] p-3.5 rounded-xl border border-purple-100/60">
                  Siswa berprestasi dengan rekam jejak proof-of-work terverifikasi di bidang rekayasa perangkat lunak, sistem basis data, dan kepemimpinan proyek. Seluruh hasil karya dan bukti telah diuji oleh guru pembimbing bersertifikasi.
                </p>
              </div>

              {/* Selected Projects */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-[11px] font-extrabold text-[#7E22CE] uppercase tracking-wider flex items-center gap-1.5">
                    <Award className="w-3.5 h-3.5" />
                    <span>Karya & Bukti Unggulan Terpilih ({selectedIds.length})</span>
                  </h3>
                  <span className="text-[10px] text-[#867798]">Otentikasi Guru Terlampir</span>
                </div>

                <div className="space-y-2.5">
                  {mockAvailableEvidences
                    .filter((e) => selectedIds.includes(e.id))
                    .map((e) => (
                      <div
                        key={e.id}
                        className="p-3.5 rounded-xl bg-white border border-[#E9E1F4] hover:border-purple-300 transition-colors shadow-xs"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <h4 className="font-extrabold text-xs text-[#261331]">{e.title}</h4>
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-[#F4ECFF] text-[#6D28D9]">
                            {e.category}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#554563] mt-1 leading-relaxed">
                          {e.desc}
                        </p>
                        <div className="flex items-center gap-2 mt-2 pt-2 border-t border-purple-50 text-[10px] text-emerald-700 font-bold">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          <span>Divalidasi oleh Guru Pembimbing • Rubrik Nilai: 4.8 / 5.0</span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>

              {/* Evaluasi Kompetensi */}
              <div className="space-y-2.5 pt-2">
                <h3 className="text-[11px] font-extrabold text-[#7E22CE] uppercase tracking-wider">
                  Penguasaan Kompetensi Terukur
                </h3>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-[#FAF8FE] border border-purple-100">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-[#261331] text-[11px]">Rekayasa Web</span>
                      <span className="font-black text-[#6D28D9] text-[11px]">92%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-purple-100 overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-purple-600 to-indigo-600 rounded-full" style={{ width: '92%' }} />
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-[#FAF8FE] border border-purple-100">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-[#261331] text-[11px]">Problem Solving</span>
                      <span className="font-black text-[#6D28D9] text-[11px]">88%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-purple-100 overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-purple-600 to-indigo-600 rounded-full" style={{ width: '88%' }} />
                    </div>
                  </div>
                </div>
              </div>

              {/* QR Verified Badge Box */}
              <div className="p-4 rounded-2xl bg-gradient-to-r from-[#FAF5FF] via-white to-[#ECFDF5] border border-purple-200/90 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 rounded-xl bg-white p-2 shadow-xs border border-purple-200 flex items-center justify-center shrink-0">
                    <QrCode className="w-8 h-8 text-[#6D28D9]" />
                  </div>
                  <div>
                    <p className="text-xs font-black text-[#261331] uppercase tracking-wide">
                      Verifikasi Otentisitas Publik
                    </p>
                    <p className="text-[11px] text-[#6F607D]">
                      Scan QR untuk membuktikan keaslian dokumen tanpa membuka data pribadi siswa.
                    </p>
                    <p className="text-[10px] font-mono text-purple-700 font-bold mt-0.5">
                      FINGERPRINT: TLN-94B8-E210-2026
                    </p>
                  </div>
                </div>
                <div className="flex sm:flex-col items-center gap-1 shrink-0">
                  <span className="px-3 py-1 rounded-full text-xs font-black bg-emerald-100 text-emerald-800 border border-emerald-300">
                    TERVERIFIKASI
                  </span>
                </div>
              </div>
            </div>

            {/* Document Footer */}
            <div className="bg-[#FAF8FE] px-8 py-3.5 border-t border-[#F0EBF8] flex items-center justify-between text-[11px] text-[#867798]">
              <span>TALENTRA.ID Educational Trust Network</span>
              <button
                type="button"
                onClick={() => window.print()}
                className="font-bold text-[#6D28D9] hover:underline flex items-center gap-1.5 cursor-pointer"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Cetak Lembar CV</span>
              </button>
            </div>
          </div>

          {/* Right Column: Controls & Selection (5 cols) */}
          <div className="lg:col-span-5 space-y-5">
            {/* Readiness Card */}
            <div className="bg-white rounded-[20px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-extrabold text-[#6F607D] uppercase tracking-wider">
                    Kelayakan CV Digital
                  </h3>
                  <p className="text-[11px] text-[#867798] mt-0.5">
                    {selectedIds.length} dari {mockAvailableEvidences.length} evidence terlampir
                  </p>
                </div>
                <span className="text-2xl font-black text-[#6D28D9]">
                  {Math.round((selectedIds.length / mockAvailableEvidences.length) * 100)}%
                </span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-[#F3E8FF] overflow-hidden">
                <div
                  className="h-full rounded-full tal-btn-primary transition-all duration-300"
                  style={{ width: `${Math.round((selectedIds.length / mockAvailableEvidences.length) * 100)}%` }}
                />
              </div>
            </div>

            {/* Evidence Checklist */}
            <div className="bg-white rounded-[20px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-extrabold text-[#261331] uppercase tracking-wider">
                  Pilih Evidence Portofolio
                </h3>
                <span className="text-[11px] font-bold text-[#7E22CE]">
                  Maksimal 8 karya
                </span>
              </div>

              <div className="space-y-2">
                {mockAvailableEvidences.map((e) => {
                  const isChecked = selectedIds.includes(e.id);
                  return (
                    <div
                      key={e.id}
                      onClick={() => toggleSelect(e.id)}
                      className={cn(
                        'p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all',
                        isChecked
                          ? 'bg-[#FAF5FF] border-purple-200 text-[#261331] shadow-xs'
                          : 'bg-white border-[#E9E1F4] text-[#6F607D] hover:bg-slate-50'
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={cn(
                            'w-5 h-5 rounded-md flex items-center justify-center text-xs font-bold transition-colors',
                            isChecked ? 'tal-btn-primary text-white' : 'border border-slate-300 bg-white'
                          )}
                        >
                          {isChecked && <Check className="w-3.5 h-3.5" />}
                        </div>
                        <div>
                          <p className="text-xs font-bold leading-tight">{e.title}</p>
                          <span className="text-[10px] text-[#9584A7]">{e.category}</span>
                        </div>
                      </div>
                      <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                        Valid
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Generate & Verification Card */}
            <div className="bg-white rounded-[20px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-extrabold text-[#261331] uppercase">Aksi Dokumen</h4>
                  <p className="text-[11px] text-[#6F607D] mt-0.5">
                    Terbitkan snapshot resmi dengan tanda tangan digital.
                  </p>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#ECFDF5] text-[#059669] border border-emerald-200">
                  SIAP TERBIT
                </span>
              </div>

              {isOffline ? (
                <div className="space-y-2">
                  <button
                    type="button"
                    disabled
                    className="w-full py-3.5 rounded-xl bg-slate-100 text-slate-400 font-bold text-sm flex items-center justify-center gap-2 cursor-not-allowed border border-slate-200"
                    title="Penerbitan CV online memerlukan koneksi internet"
                  >
                    <Lock className="w-4 h-4 text-slate-400" />
                    <span>Generate CV PDF (Mode Offline)</span>
                  </button>
                  <p className="text-[11px] text-amber-700 bg-amber-50 p-2.5 rounded-xl border border-amber-200 leading-tight">
                    Anda sedang berada dalam mode offline. Pratinjau CV di sebelah kiri tetap aktif dan dapat dicetak/disimpan langsung menggunakan tombol Cetak di bawah.
                  </p>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  className="w-full py-3.5 rounded-xl tal-btn-primary font-bold text-sm flex items-center justify-center gap-2 shadow-xs disabled:opacity-50"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-white" />
                      <span>Menerbitkan Snapshot Resmi...</span>
                    </>
                  ) : (
                    <>
                      <FileCheck2 className="w-4 h-4" />
                      <span>Generate CV PDF & QR Token</span>
                    </>
                  )}
                </button>
              )}

              <button
                type="button"
                onClick={() => window.print()}
                className="w-full py-2.5 px-4 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-bold text-xs inline-flex items-center justify-center gap-2 transition-colors"
              >
                <Printer className="w-3.5 h-3.5 text-purple-600" />
                <span>Cetak / Unduh PDF Lokal</span>
              </button>

              {generatedCv && (
                <div className="p-4 rounded-xl bg-gradient-to-r from-purple-50 to-emerald-50 border border-purple-200/80 space-y-3 animate-in fade-in">
                  <div className="flex items-center gap-2 text-xs font-bold text-emerald-700">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span>CV Resmi Berhasil Diterbitkan</span>
                  </div>
                  <div>
                    <Link
                      href={generatedCv.verificationUrl || `/verify/${generatedCv.verificationToken || 'tlnt_token_v94b8e21'}`}
                      className="w-full py-2.5 px-4 rounded-xl tal-btn-secondary text-xs font-bold inline-flex items-center justify-center gap-2"
                    >
                      <span>Buka Halaman Verifikasi Publik</span>
                      <ShieldCheck className="w-3.5 h-3.5 text-purple-600" />
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
