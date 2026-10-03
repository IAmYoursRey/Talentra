'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../services/auth.service';
import { UserRole } from '../../types/auth.types';
import {
  Eye,
  EyeOff,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Award,
  Layers,
  CheckCircle2,
  X,
  Compass,
  FileCheck2,
  User,
  GraduationCap,
  Loader2,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { PageLoadingCover } from '../../components/common/PageLoadingCover';

type SubmittingTarget = 'student' | 'teacher' | 'admin' | 'form' | null;

export default function LoginPage() {
  const router = useRouter();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittingTarget, setSubmittingTarget] = useState<SubmittingTarget>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [showFlowModal, setShowFlowModal] = useState(false);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim()) {
      setErrorMsg('ID Resmi (NISN / NUPTK / NIP / NPSN) wajib diisi.');
      return;
    }
    setErrorMsg('');
    setIsSubmitting(true);
    setSubmittingTarget('form');

    try {
      const res = await authService.login(identifier, password);
      router.push(res.redirectTo);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'ID pengguna atau kata sandi tidak sesuai.';
      setErrorMsg(msg);
      setIsSubmitting(false);
      setSubmittingTarget(null);
    }
  };

  const handleQuickRole = async (role: UserRole) => {
    if (submittingTarget) return;
    setIsSubmitting(true);
    setSubmittingTarget(role);
    setErrorMsg('');
    const demoCreds: Record<UserRole, { id: string; pwd: string }> = {
      student: { id: '0081234567', pwd: 'PasswordSiswa123!' },
      teacher: { id: '198501012010011001', pwd: 'PasswordGuru123!' },
      admin: { id: 'raihanansari6678@gmail.com', pwd: 'raihanansari6678@gmail.com' },
    };
    const cred = demoCreds[role];
    if (cred) {
      setIdentifier(cred.id);
      setPassword(cred.pwd);
    }
    try {
      const res = await authService.demoLogin(role);
      router.push(res.redirectTo);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal mengakses akun demo.';
      setErrorMsg(msg);
      setIsSubmitting(false);
      setSubmittingTarget(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#FCFBFF] flex flex-col justify-between font-sans selection:bg-[#8B5CF6] selection:text-white">
      <div className="flex-1 flex flex-col lg:flex-row min-h-screen">
        {/* Left Hero Pane matching 01-Landing-Login-HF-v2.svg */}
        <div className="lg:w-[58%] bg-gradient-to-br from-[#2E1065] via-[#4C1D95] to-[#6D28D9] p-8 sm:p-12 lg:p-16 flex flex-col justify-between text-white relative overflow-hidden">
          {/* Decorative Glowing Elements */}
          <div className="absolute top-16 right-16 w-72 h-72 rounded-full bg-[#6D28D9]/40 blur-3xl pointer-events-none" />
          <div className="absolute bottom-20 left-10 w-80 h-80 rounded-full bg-[#A855F7]/20 blur-3xl pointer-events-none" />
          <div className="absolute top-36 right-28 w-28 h-28 rounded-full bg-gradient-to-br from-[#8B5CF6] to-[#C084FC] opacity-40 blur-xl pointer-events-none" />

          {/* Top Brand Header */}
          <div className="relative z-10">
            <div className="flex items-center gap-3">
              <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-[#6D28D9] via-[#8B5CF6] to-[#A855F7] flex items-center justify-center font-black text-white text-lg shadow-lg">
                T
                <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-[#C084FC] ring-2 ring-[#2E1065]" />
              </div>
              <span className="font-extrabold text-2xl tracking-tight text-white">
                TALENTRA<span className="text-[#C084FC]">.ID</span>
              </span>
            </div>

            {/* Badge & Big Title */}
            <div className="mt-12 space-y-6 max-w-xl">
              <div className="inline-flex items-center px-4 py-1.5 rounded-full bg-[#4C1D95] border border-purple-400/30 text-[#E9D5FF] text-xs font-bold tracking-wider uppercase shadow-xs">
                PORTOFOLIO DIGITAL SISWA
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white leading-tight tracking-tight">
                Bukti nyata kemampuan <br />
                lebih kuat daripada <br />
                sekadar angka.
              </h1>

              <p className="text-[#D9CDE5] text-sm sm:text-base leading-relaxed max-w-lg">
                Karya siswa divalidasi guru, dipetakan menjadi skill, lalu diterjemahkan menjadi arah studi dan CV terverifikasi.
              </p>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => document.getElementById('identifier')?.focus()}
                  className="px-5 py-3 rounded-xl tal-btn-primary font-bold text-xs sm:text-sm shadow-lg shadow-purple-950/30"
                >
                  Mulai eksplorasi
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickRole('student')}
                  disabled={Boolean(submittingTarget)}
                  className="px-5 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-400 hover:to-indigo-400 text-white font-bold text-xs sm:text-sm transition-all shadow-md flex items-center gap-1.5 disabled:opacity-50"
                >
                  {submittingTarget === 'student' ? (
                    <Loader2 className="w-4 h-4 animate-spin text-white" />
                  ) : (
                    <Sparkles className="w-4 h-4 text-amber-300" />
                  )}
                  <span>
                    {submittingTarget === 'student'
                      ? 'Memuat Akun Siswa...'
                      : 'Masuk Akun Demo (1-Klik)'}
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => setShowFlowModal(true)}
                  className="px-5 py-3 rounded-xl bg-[#3B1768]/80 hover:bg-[#4C1D95] border border-[#604C70] text-white font-bold text-xs sm:text-sm transition-all shadow-xs"
                >
                  Lihat alur
                </button>
              </div>
            </div>
          </div>

          {/* Proof of Work Card */}
          <div className="relative z-10 mt-12 pt-6">
            <div className="bg-[#32145B]/90 border border-[#4C1D95] rounded-2xl p-5 sm:p-6 backdrop-blur-md flex flex-col sm:flex-row sm:items-center justify-between gap-4 max-w-xl shadow-lg">
              <div>
                <span className="text-[10px] font-extrabold text-[#D8B4FE] tracking-widest uppercase block mb-1">
                  PROOF OF WORK
                </span>
                <p className="text-base sm:text-lg font-extrabold text-white">
                  Satu identitas talenta dari karya nyata.
                </p>
              </div>
              <div className="px-4 py-2 rounded-xl bg-white/10 border border-white/10 text-white text-xs font-bold flex items-center gap-2 self-start sm:self-auto shrink-0">
                <Award className="w-4 h-4 text-[#C084FC]" />
                <span>Project & Evidence</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Login Pane matching 01-Landing-Login-HF-v2.svg */}
        <div className="lg:w-[42%] flex items-center justify-center p-6 sm:p-10 lg:p-14 bg-[#FCFBFF]">
          <div className="w-full max-w-md bg-white rounded-[26px] border border-[#E9E1F4] p-8 sm:p-10 shadow-[0_10px_30px_rgba(76,29,149,0.08)] space-y-6">
            <div>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
                Selamat datang
              </h2>
              <p className="text-xs sm:text-sm text-[#6F607D] mt-1.5">
                Masuk menggunakan ID resmi sekolah.
              </p>
            </div>

            {errorMsg && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="identifier"
                  className="block text-xs font-bold text-[#6F607D] mb-1.5"
                >
                  ID Resmi
                </label>
                <input
                  id="identifier"
                  type="text"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="NISN / NUPTK / NIP / NPSN"
                  className="w-full px-4 py-3 bg-white border border-[#E9E1F4] rounded-xl text-sm text-[#261331] placeholder-[#9584A7] focus:outline-none focus:ring-2 focus:ring-[#8B5CF6] focus:border-transparent transition-all"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label
                    htmlFor="password"
                    className="block text-xs font-bold text-[#6F607D]"
                  >
                    Password
                  </label>
                  <button
                    type="button"
                    onClick={() => alert('Pemulihan password dapat dilakukan melalui admin sekolah Anda.')}
                    className="text-xs text-[#6D28D9] hover:text-[#8B5CF6] font-bold"
                  >
                    Lupa password?
                  </button>
                </div>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full px-4 py-3 bg-white border border-[#E9E1F4] rounded-xl text-sm text-[#261331] placeholder-[#9584A7] focus:outline-none focus:ring-2 focus:ring-[#8B5CF6] focus:border-transparent transition-all pr-11"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? 'Sembunyikan password' : 'Lihat password'}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9584A7] hover:text-[#261331] p-1"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={Boolean(submittingTarget)}
                className="w-full py-3.5 px-4 rounded-xl tal-btn-primary font-bold text-sm tracking-wide shadow-md flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
              >
                {submittingTarget === 'form' ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-white" />
                    <span>Memvalidasi Sesi...</span>
                  </>
                ) : (
                  <>
                    <span>Masuk ke TALENTRA</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            {/* Direct Demo Account Logins */}
            <div id="demo-accounts" className="pt-5 border-t border-[#E9E1F4] space-y-3.5">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-extrabold text-[#261331] tracking-tight">
                    Masuk dengan Akun Demo
                  </h3>
                  <p className="text-[11px] text-[#6F607D]">
                    Pilih akun demo untuk langsung masuk dan mencoba fitur:
                  </p>
                </div>
                <span className="text-[10px] uppercase font-black text-[#6D28D9] bg-purple-100 px-2 py-0.5 rounded-full border border-purple-200">
                  1-Klik Masuk
                </span>
              </div>

              {/* 3 Dedicated Demo Account Cards */}
              <div className="space-y-2.5">
                {/* 1. Akun Siswa */}
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => handleQuickRole('student')}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleQuickRole('student');
                    }
                  }}
                  className={cn(
                    'bg-[#FAF7FD] hover:bg-[#F3E8FF] border rounded-2xl p-3.5 transition-all shadow-xs flex items-center justify-between gap-3 group cursor-pointer focus-visible:ring-2 focus-visible:ring-[#8B5CF6]',
                    submittingTarget === 'student'
                      ? 'border-[#8B5CF6] ring-2 ring-purple-200 bg-[#F3E8FF]'
                      : 'border-[#E9E1F4] hover:border-[#8B5CF6]',
                    Boolean(submittingTarget && submittingTarget !== 'student') && 'opacity-60 pointer-events-none'
                  )}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-purple-100 text-[#6D28D9] flex items-center justify-center font-bold text-sm shrink-0 group-hover:scale-105 transition-transform">
                      {submittingTarget === 'student' ? (
                        <Loader2 className="w-5 h-5 animate-spin text-[#6D28D9]" />
                      ) : (
                        <User className="w-5 h-5" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-[#261331] truncate">Siswa Demo</span>
                        <span className="text-[9px] font-extrabold px-1.5 py-0.2 bg-blue-100 text-blue-700 rounded-md">SISWA</span>
                      </div>
                      <p className="text-[11px] text-[#6F607D] truncate">NISN: 0081234567 • XII RPL 1</p>
                    </div>
                  </div>
                  <div
                    className={cn(
                      'px-3.5 py-2 rounded-xl text-white text-xs font-bold shadow-xs transition-all shrink-0 flex items-center gap-1.5',
                      submittingTarget === 'student' ? 'bg-[#5B21B6]' : 'bg-[#6D28D9] group-hover:bg-[#5B21B6]'
                    )}
                  >
                    {submittingTarget === 'student' ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                        <span>Memuat...</span>
                      </>
                    ) : (
                      <>
                        <span>Masuk</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </div>
                </div>

                {/* 2. Akun Guru */}
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => handleQuickRole('teacher')}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleQuickRole('teacher');
                    }
                  }}
                  className={cn(
                    'bg-[#FAF7FD] hover:bg-[#ECFDF5] border rounded-2xl p-3.5 transition-all shadow-xs flex items-center justify-between gap-3 group cursor-pointer focus-visible:ring-2 focus-visible:ring-emerald-500',
                    submittingTarget === 'teacher'
                      ? 'border-emerald-500 ring-2 ring-emerald-200 bg-[#ECFDF5]'
                      : 'border-[#E9E1F4] hover:border-emerald-400',
                    Boolean(submittingTarget && submittingTarget !== 'teacher') && 'opacity-60 pointer-events-none'
                  )}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-sm shrink-0 group-hover:scale-105 transition-transform">
                      {submittingTarget === 'teacher' ? (
                        <Loader2 className="w-5 h-5 animate-spin text-emerald-700" />
                      ) : (
                        <GraduationCap className="w-5 h-5" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-[#261331] truncate">Guru Demo</span>
                        <span className="text-[9px] font-extrabold px-1.5 py-0.2 bg-emerald-100 text-emerald-800 rounded-md">GURU</span>
                      </div>
                      <p className="text-[11px] text-[#6F607D] truncate">NIP: 19850101... • Pembimbing 3 Kelas</p>
                    </div>
                  </div>
                  <div
                    className={cn(
                      'px-3.5 py-2 rounded-xl text-white text-xs font-bold shadow-xs transition-all shrink-0 flex items-center gap-1.5',
                      submittingTarget === 'teacher' ? 'bg-emerald-700' : 'bg-emerald-600 group-hover:bg-emerald-700'
                    )}
                  >
                    {submittingTarget === 'teacher' ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                        <span>Memuat...</span>
                      </>
                    ) : (
                      <>
                        <span>Masuk</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </div>
                </div>

                {/* 3. Akun Admin */}
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => handleQuickRole('admin')}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleQuickRole('admin');
                    }
                  }}
                  className={cn(
                    'bg-[#FAF7FD] hover:bg-[#F3E8FF] border rounded-2xl p-3.5 transition-all shadow-xs flex items-center justify-between gap-3 group cursor-pointer focus-visible:ring-2 focus-visible:ring-purple-500',
                    submittingTarget === 'admin'
                      ? 'border-purple-500 ring-2 ring-purple-200 bg-[#F3E8FF]'
                      : 'border-[#E9E1F4] hover:border-purple-400',
                    Boolean(submittingTarget && submittingTarget !== 'admin') && 'opacity-60 pointer-events-none'
                  )}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-purple-100 text-[#9333EA] flex items-center justify-center font-bold text-sm shrink-0 group-hover:scale-105 transition-transform">
                      {submittingTarget === 'admin' ? (
                        <Loader2 className="w-5 h-5 animate-spin text-[#9333EA]" />
                      ) : (
                        <ShieldCheck className="w-5 h-5" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-[#261331] truncate">Admin Demo</span>
                        <span className="text-[9px] font-extrabold px-1.5 py-0.2 bg-purple-100 text-purple-800 rounded-md">ADMIN</span>
                      </div>
                      <p className="text-[11px] text-[#6F607D] truncate">Admin Sekolah • SMKN 1 Jakarta</p>
                    </div>
                  </div>
                  <div
                    className={cn(
                      'px-3.5 py-2 rounded-xl text-white text-xs font-bold shadow-xs transition-all shrink-0 flex items-center gap-1.5',
                      submittingTarget === 'admin' ? 'bg-[#7E22CE]' : 'bg-[#9333EA] group-hover:bg-[#7E22CE]'
                    )}
                  >
                    {submittingTarget === 'admin' ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                        <span>Memuat...</span>
                      </>
                    ) : (
                      <>
                        <span>Masuk</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 29-End-to-End-Flow-HF Modal */}
      {showFlowModal && (
        <div
          className="fixed inset-0 z-50 bg-[#261331]/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in"
          onClick={() => setShowFlowModal(false)}
        >
          <div
            className="bg-white rounded-3xl border border-[#E9E1F4] max-w-4xl w-full p-6 sm:p-8 shadow-2xl space-y-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-4 border-b border-[#E9E1F4]">
              <div>
                <h3 className="text-xl font-extrabold text-[#261331]">End-to-End User Flow</h3>
                <p className="text-xs text-[#6F607D] mt-0.5">
                  Alur inti TALENTRA.ID dari login sampai verifikasi publik.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowFlowModal(false)}
                className="p-1.5 rounded-xl text-[#9584A7] hover:text-[#261331] hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* 7 Flow Steps matching 29-End-to-End-Flow-HF.svg */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-3">
              {[
                { step: '1', title: 'Login', sub: 'Role otomatis', detail: 'NISN / NUPTK' },
                { step: '2', title: 'Upload', sub: 'Proof of Work', detail: 'File + 3–5 tags' },
                { step: '3', title: 'Review', sub: 'Guru validasi', detail: 'Endorse / Revise' },
                { step: '4', title: 'Skill Map', sub: 'Approved only', detail: 'Radar + provenance' },
                { step: '5', title: 'Career', sub: 'Evidence-based', detail: 'Study + career' },
                { step: '6', title: 'Digital CV', sub: 'PDF + QR', detail: 'Snapshot + QR' },
                { step: '7', title: 'Verify', sub: 'Verified / Revoked', detail: 'Public status' },
              ].map((item) => (
                <div
                  key={item.step}
                  className="bg-[#FCFBFF] border border-[#E9E1F4] rounded-2xl p-3.5 text-center flex flex-col justify-between"
                >
                  <div className="w-6 h-6 rounded-full tal-btn-primary font-bold text-xs flex items-center justify-center mx-auto mb-2">
                    {item.step}
                  </div>
                  <h4 className="text-xs font-extrabold text-[#261331]">{item.title}</h4>
                  <p className="text-[10px] text-[#6D28D9] font-bold mt-0.5">{item.sub}</p>
                  <p className="text-[9px] text-[#6F607D] mt-1">{item.detail}</p>
                </div>
              ))}
            </div>

            <div className="p-3 rounded-xl bg-[#F7F2FF] text-center border border-purple-100">
              <p className="text-xs font-semibold text-[#6D28D9]">
                Navigasi tidak berpindah posisi; hanya active state dan konten utama yang berubah.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
