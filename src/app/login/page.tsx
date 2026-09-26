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
  BarChart3,
  User,
  GraduationCap,
} from 'lucide-react';
import Link from 'next/link';

export default function LoginPage() {
  const router = useRouter();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim()) {
      setErrorMsg('ID Pengguna / Nomor Identitas wajib diisi.');
      return;
    }
    setErrorMsg('');
    setIsSubmitting(true);

    try {
      const res = await authService.login(identifier, password);
      router.push(res.redirectTo);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'ID pengguna atau kata sandi tidak sesuai.';
      setErrorMsg(msg);
      setIsSubmitting(false);
    }
  };

  const handleQuickDemo = async (role: UserRole) => {
    setIsSubmitting(true);
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
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      <div className="flex-1 flex flex-col lg:flex-row">
        {/* Left Hero / Brand Pane (Desktop) */}
        <div className="lg:w-1/2 bg-gradient-to-br from-slate-900 via-slate-800 to-brand-950 p-8 sm:p-12 lg:p-16 flex flex-col justify-between text-white relative overflow-hidden">
          {/* Decorative subtle background grid */}
          <div className="absolute inset-0 bg-[radial-gradient(#3157D5_1px,transparent_1px)] [background-size:24px_24px] opacity-15" />

          <div className="relative z-10">
            {/* Logo */}
            <div className="flex items-center gap-2.5 mb-12">
              <div className="w-10 h-10 rounded-xl bg-brand-500 text-white flex items-center justify-center font-extrabold text-xl shadow-lg">
                T
              </div>
              <div>
                <span className="font-extrabold text-xl tracking-tight text-white">
                  TALENTRA<span className="text-brand-400">.ID</span>
                </span>
                <span className="block text-[11px] text-slate-300 font-medium tracking-wider uppercase">
                  Smart Digital Portfolio
                </span>
              </div>
            </div>

            {/* Headline */}
            <div className="max-w-md space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/20 border border-brand-400/30 text-brand-300 text-xs font-semibold">
                <Sparkles className="w-3.5 h-3.5 text-brand-400" />
                <span>Next-Gen Education SaaS</span>
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight">
                Portofolio nyata. <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-300 via-growth-300 to-white">
                  Talenta yang terlihat.
                </span>
              </h1>

              <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
                Dokumentasikan karya, kembangkan bukti kompetensi dengan validasi guru terstruktur, dan temukan rekomendasi studi dan karier berbasis data objektif.
              </p>
            </div>
          </div>

          {/* Pillars feature badges */}
          <div className="relative z-10 mt-12 grid grid-cols-1 sm:grid-cols-3 gap-4 pt-8 border-t border-slate-700/60">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-white/10 text-growth-400">
                <Award className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-white">Proof of Work</p>
                <p className="text-[11px] text-slate-400">Karya terverifikasi guru</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-white/10 text-brand-400">
                <BarChart3 className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-white">Skill Mapping</p>
                <p className="text-[11px] text-slate-400">Radar talenta deterministik</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-white/10 text-emerald-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-white">Digital CV & QR</p>
                <p className="text-[11px] text-slate-400">Otentisitas resmi sekolah</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Form Pane */}
        <div className="lg:w-1/2 flex items-center justify-center p-6 sm:p-12 lg:p-16 bg-white">
          <div className="w-full max-w-md space-y-8">
            <div>
              <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                Masuk ke Akun Anda
              </h2>
              <p className="text-xs sm:text-sm text-slate-500 mt-1">
                Gunakan ID akun sekolah atau pilih mode akses demo untuk evaluasi.
              </p>
            </div>

            {errorMsg && (
              <div className="p-3 rounded-lg bg-reject-50 border border-reject-200 text-reject-700 text-xs font-medium">
                {errorMsg}
              </div>
            )}

            {/* Standard Login Form */}
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="identifier"
                  className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
                >
                  ID Pengguna / Email / Nomor Identitas
                </label>
                <input
                  id="identifier"
                  type="text"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder="Contoh: raihanansari6678@gmail.com, NISN, NUPTK/NIP, atau NPSN"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label
                    htmlFor="password"
                    className="block text-xs font-semibold text-slate-700 uppercase tracking-wider"
                  >
                    Kata Sandi
                  </label>
                  <button
                    type="button"
                    onClick={() => alert('Fitur pemulihan kata sandi melalui operator sekolah akan hadir pada Phase 2.')}
                    className="text-xs text-brand-600 hover:text-brand-700 font-medium"
                  >
                    Lupa sandi?
                  </button>
                </div>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? 'Sembunyikan kata sandi' : 'Tampilkan kata sandi'}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1 rounded"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="rounded border-slate-300 text-brand-600 focus:ring-brand-500 w-4 h-4"
                  />
                  <span className="text-xs text-slate-600 select-none">Ingat sesi di perangkat ini</span>
                </label>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-semibold text-sm transition-colors shadow-xs focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:opacity-50"
              >
                <span>{isSubmitting ? 'Memproses...' : 'Masuk ke Platform'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>

            {/* SEPARATED DEMO ACCESS SECTION */}
            <div className="pt-6 border-t-2 border-dashed border-slate-200">
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1 text-[11px] font-bold text-brand-700 bg-brand-100/70 px-2 py-0.5 rounded">
                    <Sparkles className="w-3 h-3 text-brand-600" />
                    AKSES DEMO & EVALUASI RESMI
                  </span>
                  <span className="text-[10px] text-emerald-700 font-semibold bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded">Live Server Auth</span>
                </div>
                <p className="text-xs text-slate-500">
                  Klik peran di bawah untuk otomatis mengisi kredensial resmi dan masuk ke platform:
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => handleQuickDemo('student')}
                    className="flex flex-col items-center justify-center p-2.5 rounded-lg bg-white border border-slate-200 hover:border-brand-500 hover:bg-brand-50/50 text-slate-800 transition-all text-center group"
                  >
                    <User className="w-5 h-5 text-brand-500 mb-1 group-hover:scale-110 transition-transform" />
                    <span className="text-xs font-bold">Demo Siswa</span>
                    <span className="text-[10px] text-slate-500 font-medium">Alya Rahma</span>
                    <span className="text-[9px] text-slate-400 font-mono mt-0.5">NISN: 0081234567</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleQuickDemo('teacher')}
                    className="flex flex-col items-center justify-center p-2.5 rounded-lg bg-white border border-slate-200 hover:border-growth-500 hover:bg-growth-50/50 text-slate-800 transition-all text-center group"
                  >
                    <GraduationCap className="w-5 h-5 text-growth-600 mb-1 group-hover:scale-110 transition-transform" />
                    <span className="text-xs font-bold">Demo Guru</span>
                    <span className="text-[10px] text-slate-500 font-medium">Pak Budi Santoso</span>
                    <span className="text-[9px] text-slate-400 font-mono mt-0.5">NIP: 19850101...</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleQuickDemo('admin')}
                    className="flex flex-col items-center justify-center p-2.5 rounded-lg bg-white border border-slate-200 hover:border-intelligence-500 hover:bg-intelligence-50/50 text-slate-800 transition-all text-center group"
                  >
                    <ShieldCheck className="w-5 h-5 text-intelligence-600 mb-1 group-hover:scale-110 transition-transform" />
                    <span className="text-xs font-bold">Demo Admin</span>
                    <span className="text-[10px] text-slate-500 font-medium">Raihan Ansari</span>
                    <span className="text-[9px] text-slate-400 font-mono mt-0.5">raihanansari...</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Public Verification Link */}
            <div className="text-center pt-2">
              <Link
                href="/verify/tlnt_token_v94b8e21"
                className="text-xs text-slate-500 hover:text-slate-800 hover:underline"
              >
                Butuh verifikasi dokumen CV kelulusan siswa? Buka Verifikasi Publik QR →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
