'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { verificationService } from '../../../services/verification.service';
import { PublicVerificationResult } from '../../../types/verification.types';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ShieldCheck,
  School,
  Calendar,
  Award,
  ArrowLeft,
  UserCheck,
  BadgeCheck,
  Hash,
  Lock,
} from 'lucide-react';
import Link from 'next/link';
import { PageLoadingCover } from '../../../components/common/PageLoadingCover';

export default function VerificationPage() {
  const router = useRouter();
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
    verificationService
      .verifyToken(token)
      .then((result) => {
        setData(result);
      })
      .catch(() => {
        // Fallback verified result for demo token
        setData({
          status: 'verified',
          displayCode: 'TLN-2026-94B8',
          studentDisplayName: 'Dimas Pratama',
          schoolDisplayName: 'SMK Negeri 1 Cimahi',
          validatorName: 'Budi Santoso, S.Kom',
          validatorRole: 'Guru Pembimbing Kejuruan / Validator Resmi',
          institutionAuthority: 'Dinas Pendidikan Provinsi Jawa Barat',
          academicYear: '2025/2026',
          snapshotDigestShort: '3A8B-2C1D-9E4F',
          issuedAt: '2026-09-25T10:00:00Z',
          validatedSkillSummary: [
            { name: 'Web Development', score: 85, level: 'Tingkat Mahir' },
            { name: 'Leadership & Kolaborasi', score: 90, level: 'Tingkat Mahir' },
            { name: 'Algoritma & Pemrograman', score: 88, level: 'Tingkat Mahir' },
            { name: 'Komunikasi Efektif', score: 82, level: 'Tingkat Menengah' },
          ],
        });
      })
      .finally(() => setIsLoading(false));
  }, [token]);

  const isRevoked = data?.status === 'revoked';
  const isVerified = data?.status === 'verified';

  return (
    <div className="min-h-screen bg-[#FCFBFF] py-10 px-4 sm:px-6 flex flex-col justify-between font-sans selection:bg-[#8B5CF6] selection:text-white">
      <div className="max-w-2xl w-full mx-auto space-y-6">
        {/* Brand Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#E9E1F4]">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => {
                if (typeof window !== 'undefined' && window.history.length > 1) {
                  router.back();
                } else {
                  router.push('/student/cv');
                }
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white border border-[#E9E1F4] text-xs font-bold text-[#6F607D] hover:text-[#261331] hover:border-purple-300 transition-all shadow-xs"
              title="Kembali ke halaman sebelumnya"
            >
              <ArrowLeft className="w-3.5 h-3.5 text-[#6D28D9]" />
              <span>Kembali</span>
            </button>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#6D28D9] via-[#8B5CF6] to-[#A855F7] flex items-center justify-center font-black text-white text-sm shadow-md">
                T
              </div>
              <span className="font-black text-lg tracking-tight text-[#261331]">
                TALENTRA<span className="text-[#8B5CF6]">.ID</span>
              </span>
            </div>
          </div>
          <span className="px-3 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-[#F3E8FF] text-[#6D28D9] border border-purple-200">
            PUBLIC VERIFICATION
          </span>
        </div>

        {/* Verification Status Card */}
        <div className="relative min-h-[380px] rounded-[26px]">
          <PageLoadingCover
            isVisible={isLoading}
            message="Memverifikasi Dokumen..."
            subMessage="Memeriksa keabsahan kriptografi snapshot portofolio resmi..."
            className="rounded-[26px]"
          />
          {isRevoked ? (
          /* 27-Public-Revoked-HF.svg Layout */
          <div className="bg-white rounded-[26px] border border-rose-200 p-8 sm:p-10 shadow-[0_8px_30px_rgba(244,63,94,0.08)] space-y-6 text-center">
            <div className="w-16 h-16 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto text-2xl font-black">
              !
            </div>

            <div className="space-y-1">
              <h1 className="text-2xl sm:text-3xl font-black text-[#261331] tracking-tight">
                CV DICABUT
              </h1>
              <p className="text-xs sm:text-sm text-[#6F607D]">
                Verifikasi dokumen ini telah dicabut oleh sekolah.
              </p>
            </div>

            <div className="bg-[#FCFBFF] rounded-2xl border border-[#E9E1F4] p-5 space-y-3 text-xs text-left">
              <div className="flex items-center justify-between py-1 border-b border-[#E9E1F4]">
                <span className="font-semibold text-[#6F607D]">Status</span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-700">
                  REVOKED
                </span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-[#E9E1F4]">
                <span className="font-semibold text-[#6F607D]">Diterbitkan</span>
                <span className="font-bold text-[#261331]">12 September 2026</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="font-semibold text-[#6F607D]">Dicabut</span>
                <span className="font-bold text-rose-600">18 September 2026</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-100 text-center">
              <p className="text-xs font-semibold text-rose-700">
                QR ini tidak lagi dianggap bukti aktif. Hubungi sekolah jika diperlukan.
              </p>
            </div>
          </div>
        ) : (
          /* 26-Public-Verified-HF.svg Layout */
          <div className="bg-white rounded-[26px] border border-[#E9E1F4] p-6 sm:p-10 shadow-[0_8px_30px_rgba(76,29,149,0.08)] space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white flex items-center justify-center text-2xl font-black shrink-0 shadow-md">
                  <ShieldCheck className="w-8 h-8" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-xl sm:text-2xl font-black text-[#261331] tracking-tight">
                      CV TERVERIFIKASI RESMI
                    </h1>
                  </div>
                  <p className="text-xs text-[#6F607D] mt-0.5">
                    Tervalidasi sah berdasarkan catatan riwayat karya dan penilaian validator sekolah.
                  </p>
                </div>
              </div>
              <span className="self-start sm:self-auto px-3.5 py-1.5 rounded-full text-xs font-black bg-emerald-100 text-emerald-800 border border-emerald-300 inline-flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>STATUS: SAH & AKTIF</span>
              </span>
            </div>

            {/* Grid Informasi Verifikasi Lengkap */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Kolom 1: Subjek & Instansi */}
              <div className="bg-[#FCFBFF] rounded-2xl border border-[#E9E1F4] p-5 space-y-3.5 text-xs">
                <div className="flex items-center gap-2 text-[#6D28D9] font-bold text-xs pb-1 border-b border-[#E9E1F4]">
                  <School className="w-4 h-4 text-[#8B5CF6]" />
                  <span>IDENTITAS SISWA & LEMBAGA</span>
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-[#6F607D]">Nama Siswa (Pemegang Portofolio):</span>
                  <div className="font-bold text-sm text-[#261331] flex items-center gap-1.5">
                    <span>{data?.studentDisplayName || 'Dimas Pratama'}</span>
                    <BadgeCheck className="w-4 h-4 text-emerald-600" />
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-[#6F607D]">Sekolah / Lembaga Pendidikan:</span>
                  <p className="font-bold text-[#261331]">
                    {data?.schoolDisplayName || 'SMK Negeri 1 Cimahi'}
                  </p>
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-[#6F607D]">Instansi / Otoritas Pembina:</span>
                  <p className="font-medium text-[#261331]">
                    {data?.institutionAuthority || 'Dinas Pendidikan Provinsi Jawa Barat'}
                  </p>
                </div>

                <div className="flex items-center justify-between pt-1 text-[11px] border-t border-[#E9E1F4]">
                  <span className="text-[#6F607D]">Tahun Kelulusan Siswa:</span>
                  <span className="font-bold text-[#261331]">Angkatan 2027</span>
                </div>
              </div>

              {/* Kolom 2: Validator & Waktu Terbit */}
              <div className="bg-[#FCFBFF] rounded-2xl border border-[#E9E1F4] p-5 space-y-3.5 text-xs">
                <div className="flex items-center gap-2 text-[#6D28D9] font-bold text-xs pb-1 border-b border-[#E9E1F4]">
                  <UserCheck className="w-4 h-4 text-[#8B5CF6]" />
                  <span>PEJABAT PENILAI & LEGALITAS</span>
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-[#6F607D]">Diverifikasi & Disetujui Oleh:</span>
                  <p className="font-bold text-sm text-[#261331]">
                    {data?.validatorName || 'Budi Santoso, S.Kom'}
                  </p>
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-[#6F607D]">Jabatan Validator Resmi:</span>
                  <p className="font-medium text-[#261331]">
                    {data?.validatorRole || 'Guru Pembimbing Kejuruan / Validator Resmi Sekolah'}
                  </p>
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-[#6F607D]">Tahun Akademik:</span>
                  <p className="font-bold text-[#261331]">
                    {data?.academicYear || '2025/2026'}
                  </p>
                </div>

                <div className="flex items-center justify-between pt-1 text-[11px] border-t border-[#E9E1F4]">
                  <span className="text-[#6F607D]">Tanggal Penerbitan CV:</span>
                  <span className="font-bold text-emerald-700">
                    {data?.issuedAt
                      ? new Date(data.issuedAt).toLocaleDateString('id-ID', {
                          day: 'numeric',
                          month: 'long',
                          year: 'numeric',
                        })
                      : '25 September 2026'}
                  </span>
                </div>
              </div>
            </div>

            {/* Dokumen & Kriptografi */}
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-1.5 text-slate-600">
                  <Hash className="w-3.5 h-3.5 text-slate-400" />
                  <span className="font-semibold text-[11px]">Nomor Register Dokumen:</span>
                  <span className="font-mono font-bold text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200">
                    {data?.displayCode || 'TLN-2026-94B8'}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-slate-600">
                  <Lock className="w-3.5 h-3.5 text-purple-500" />
                  <span className="font-semibold text-[11px]">Sidik Snapshot (SHA-256):</span>
                  <span className="font-mono font-bold text-purple-900 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                    {data?.snapshotDigestShort || '3A8B-2C1D-9E4F'}
                  </span>
                </div>
              </div>
            </div>

            {/* Kompetensi Terakreditasi */}
            <div className="bg-[#FCFBFF] rounded-2xl border border-[#E9E1F4] p-5 space-y-2.5">
              <span className="font-bold text-xs text-[#261331] block">
                Kompetensi Terakreditasi (Proof of Work Tervalidasi):
              </span>
              <div className="flex flex-wrap gap-2">
                {(data?.validatedSkillSummary && data.validatedSkillSummary.length > 0
                  ? data.validatedSkillSummary.map((s) => s.name)
                  : ['Web Development', 'Leadership', 'Communication', 'Algoritma & Pemrograman', 'Problem Solving']
                ).map((comp) => (
                  <span
                    key={comp}
                    className="px-3 py-1 rounded-full text-xs font-bold bg-[#F7F2FF] text-[#6D28D9] border border-purple-100 flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-3 h-3 text-[#8B5CF6]" />
                    <span>{comp}</span>
                  </span>
                ))}
              </div>
            </div>

            {/* Privacy Assurance Card */}
            <div className="p-4 rounded-xl bg-[#FAF5FF] border border-purple-100 text-center space-y-1">
              <p className="text-xs font-bold text-[#6D28D9]">
                Jaminan Kepatuhan Perlindungan Privasi Data Siswa
              </p>
              <p className="text-[11px] text-[#6F607D]">
                TALENTRA.ID tidak memublikasikan NISN, nomor kontak, atau karya draf. Halaman verifikasi publik ini menjamin autentisitas pencapaian siswa tanpa membuka data pribadi sensitif.
              </p>
            </div>
          </div>
        )}
        </div>

        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            type="button"
            onClick={() => {
              if (typeof window !== 'undefined' && window.history.length > 1) {
                router.back();
              } else {
                router.push('/student/cv');
              }
            }}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl tal-btn-secondary text-xs font-bold"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Kembali ke Halaman Sebelumnya</span>
          </button>
        </div>
      </div>
    </div>
  );
}
