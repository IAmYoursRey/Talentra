'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { verificationService } from '../../../services/verification.service';
import { PublicVerificationResult, VerificationStatus } from '../../../types/verification.types';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Shield,
  School,
  Calendar,
  Award,
  ArrowLeft,
  FileText,
  Fingerprint,
  Tag,
} from 'lucide-react';
import Link from 'next/link';
import { cn } from '../../../lib/utils';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';

export default function VerificationPage() {
  const params = useParams();
  const rawParam = params?.token;
  const token = (Array.isArray(rawParam) ? rawParam[0] : rawParam) || '';

  const [data, setData] = useState<PublicVerificationResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      setData({ status: 'invalid', message: 'Tautan tidak menyertakan token verifikasi.' });
      return;
    }
    setIsLoading(true);
    verificationService.verifyToken(token).then((result) => {
      setData(result);
      setIsLoading(false);
    });
  }, [token]);

  const statusConfigs: Record<
    VerificationStatus,
    { title: string; desc: string; icon: React.ComponentType<{ className?: string }>; bg: string; text: string; border: string }
  > = {
    verified: {
      title: 'CV Terverifikasi Resmi',
      desc: 'Dokumen ini diterbitkan dari rekam jejak karya yang telah divalidasi oleh pihak sekolah melalui platform TALENTRA.ID.',
      icon: CheckCircle2,
      bg: 'bg-emerald-50',
      text: 'text-emerald-700',
      border: 'border-emerald-300',
    },
    expired: {
      title: 'Masa Verifikasi Dokumen Telah Berakhir',
      desc: 'Masa verifikasi dokumen ini telah terlampaui. Dokumen ini tidak dapat lagi diverifikasi sebagai berkas aktif.',
      icon: AlertTriangle,
      bg: 'bg-amber-50',
      text: 'text-amber-700',
      border: 'border-amber-300',
    },
    revoked: {
      title: 'Dokumen Tidak Lagi Berlaku',
      desc: 'Keabsahan dokumen ini telah dicabut oleh pemilik atau pihak institusi sekolah.',
      icon: XCircle,
      bg: 'bg-red-50',
      text: 'text-red-700',
      border: 'border-red-300',
    },
    invalid: {
      title: 'Dokumen Tidak Ditemukan atau Tautan Tidak Valid',
      desc: 'Tautan verifikasi ini tidak valid atau tidak terdaftar dalam basis data TALENTRA.ID.',
      icon: HelpCircle,
      bg: 'bg-slate-100',
      text: 'text-slate-700',
      border: 'border-slate-300',
    },
    invalid_token: {
      title: 'Dokumen Tidak Ditemukan atau Tautan Tidak Valid',
      desc: 'Tautan verifikasi ini tidak valid atau tidak terdaftar dalam basis data TALENTRA.ID.',
      icon: HelpCircle,
      bg: 'bg-slate-100',
      text: 'text-slate-700',
      border: 'border-slate-300',
    },
  };

  const statusKey: VerificationStatus = data?.status && statusConfigs[data.status] ? data.status : 'invalid';
  const currentStatusConfig = statusConfigs[statusKey];
  const StatusIcon = currentStatusConfig.icon;

  return (
    <div className="min-h-screen bg-slate-50 py-8 sm:py-12 px-4 sm:px-6 flex flex-col justify-between font-sans">
      <div className="max-w-2xl w-full mx-auto space-y-6">
        {/* Brand header */}
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-600 text-white flex items-center justify-center font-bold text-base shadow-xs">
              T
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-slate-900">
                TALENTRA<span className="text-brand-600">.ID</span>
              </span>
              <span className="block text-[10px] text-slate-400 font-medium -mt-1 tracking-wider uppercase">
                Verifikasi Keaslian CV Digital
              </span>
            </div>
          </Link>

          <div className="flex items-center gap-1.5 text-xs text-slate-500 bg-white border border-slate-200 px-3 py-1.5 rounded-full shadow-2xs">
            <Shield className="w-3.5 h-3.5 text-emerald-600" />
            <span className="font-medium">Otoritas Digital Sekolah</span>
          </div>
        </div>

        {/* Verification Card */}
        <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="p-8">
              <LoadingSkeleton rows={6} />
            </div>
          ) : (
            <div>
              {/* Status Header Banner */}
              <div
                className={cn(
                  'p-6 sm:p-8 border-b flex items-start gap-4',
                  currentStatusConfig.bg,
                  currentStatusConfig.border
                )}
              >
                <div
                  className={cn(
                    'w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border bg-white shadow-2xs',
                    currentStatusConfig.text,
                    currentStatusConfig.border
                  )}
                >
                  <StatusIcon className="w-6 h-6" />
                </div>
                <div>
                  <h1 className={cn('text-lg sm:text-xl font-bold tracking-tight', currentStatusConfig.text)}>
                    {currentStatusConfig.title}
                  </h1>
                  <p className="text-xs sm:text-sm text-slate-600 mt-1 leading-relaxed">
                    {data?.message || currentStatusConfig.desc}
                  </p>
                  {data?.displayCode && (
                    <div className="mt-2.5 inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-white/80 border border-slate-200 text-xs font-mono font-bold text-slate-800">
                      <span>Kode Dokumen:</span>
                      <span className="text-brand-700">{data.displayCode}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Verified Details */}
              {data && data.status === 'verified' && (
                <div className="p-6 sm:p-8 space-y-6">
                  {/* Student & School Info */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pb-6 border-b border-slate-100">
                    <div>
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Nama Pemilik Dokumen
                      </p>
                      <p className="text-lg font-bold text-slate-900 mt-0.5">
                        {data.studentDisplayName}
                      </p>
                      <p className="text-xs text-emerald-700 font-medium mt-0.5">
                        ✓ Terverifikasi Siswa Aktif Sekolah
                      </p>
                    </div>

                    <div>
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        Institusi Penerbit
                      </p>
                      <p className="text-sm font-bold text-slate-900 mt-0.5 flex items-center gap-1.5">
                        <School className="w-4 h-4 text-brand-600 shrink-0" />
                        <span>{data.schoolDisplayName}</span>
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span>Diterbitkan: {new Date(data.issuedAt || '').toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
                      </p>
                    </div>
                  </div>

                  {/* Fingerprint Authenticity Checkbox */}
                  {data.snapshotDigestShort && (
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-3 text-xs">
                      <div className="flex items-center gap-2">
                        <Fingerprint className="w-4 h-4 text-brand-600 shrink-0" />
                        <span className="text-slate-600">Sidik Jari Snapshot (SHA-256):</span>
                      </div>
                      <span className="font-mono font-bold text-slate-800 bg-white px-2 py-0.5 rounded border border-slate-200">
                        {data.snapshotDigestShort}
                      </span>
                    </div>
                  )}

                  {/* Validated Skills Summary */}
                  {data.validatedSkillSummary && data.validatedSkillSummary.length > 0 && (
                    <div className="space-y-3">
                      <p className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                        <Award className="w-4 h-4 text-brand-600" />
                        <span>Keterampilan Tervalidasi</span>
                      </p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {data.validatedSkillSummary.map((sk, idx) => (
                          <div
                            key={idx}
                            className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between"
                          >
                            <span className="text-xs font-bold text-slate-800">{sk.name}</span>
                            <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                              {sk.level || `Skor: ${sk.score}`}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Selected Portfolios Published in CV */}
                  {data.selectedPortfolioSummaries && data.selectedPortfolioSummaries.length > 0 && (
                    <div className="space-y-3 pt-2">
                      <p className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                        <FileText className="w-4 h-4 text-brand-600" />
                        <span>Karya Tervalidasi dalam Dokumen</span>
                      </p>
                      <div className="space-y-2.5">
                        {data.selectedPortfolioSummaries.map((proj, idx) => (
                          <div
                            key={idx}
                            className="p-3.5 rounded-xl border border-slate-200 space-y-1.5 bg-white"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <h3 className="text-xs font-bold text-slate-900">{proj.title}</h3>
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
                                Disetujui Guru
                              </span>
                            </div>
                            <p className="text-xs text-slate-600 line-clamp-2">
                              {proj.description}
                            </p>
                            {proj.tags && proj.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1 pt-1">
                                {proj.tags.map((t, tidx) => (
                                  <span
                                    key={tidx}
                                    className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600 font-medium"
                                  >
                                    <Tag className="w-2.5 h-2.5" />
                                    <span>{t}</span>
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Privacy Assurance Notice */}
                  <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-500 space-y-1">
                    <p className="font-semibold text-slate-700">Perlindungan Privasi Pelajar:</p>
                    <p className="text-[11px] leading-relaxed">
                      Sesuai standar perlindungan data pelajar TALENTRA.ID, nomor identitas resmi siswa (NISN), NIP guru, NPSN sekolah, serta dokumen internal tidak dipublikasikan ke publik.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="text-center">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 font-medium transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Kembali ke Beranda TALENTRA.ID</span>
          </Link>
        </div>
      </div>

      <footer className="mt-8 text-center text-xs text-slate-400">
        &copy; 2026 TALENTRA.ID &bull; Platform Portofolio Digital Pintar Sekolah Indonesia
      </footer>
    </div>
  );
}
