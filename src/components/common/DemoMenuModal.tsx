'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../services/auth.service';
import { UserRole } from '../../types/auth.types';
import {
  Sparkles,
  X,
  User,
  GraduationCap,
  ShieldCheck,
  CheckCircle2,
  FolderPlus,
  Layers,
  Compass,
  FileCheck2,
  CheckSquare,
  BarChart3,
  Users,
  Settings,
  QrCode,
  ArrowRight,
  ExternalLink,
  BookOpen,
  Award,
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface DemoMenuModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentRole?: UserRole;
}

interface FeatureItem {
  id: string;
  title: string;
  category: 'student' | 'teacher' | 'admin' | 'public';
  description: string;
  route: string;
  requiredRole?: UserRole;
  isExternal?: boolean;
  badge?: string;
  icon: React.ComponentType<{ className?: string }>;
}

const DEMO_FEATURES: FeatureItem[] = [
  // Siswa
  {
    id: 'std-dashboard',
    title: 'Dashboard Siswa',
    category: 'student',
    requiredRole: 'student',
    route: '/student',
    description: 'Ringkasan capaian, radar talenta terkini, dan panduan tahapan portofolio.',
    icon: User,
  },
  {
    id: 'std-upload',
    title: 'Unggah Bukti Karya (Proof of Work)',
    category: 'student',
    requiredRole: 'student',
    route: '/student/portfolio/new',
    description: 'Form submission portofolio dengan 3–5 canonical tags, berkas bukti, dan tautan karya.',
    badge: 'Inti',
    icon: FolderPlus,
  },
  {
    id: 'std-portfolio-list',
    title: 'Manajemen & Riwayat Portofolio',
    category: 'student',
    requiredRole: 'student',
    route: '/student/portfolio',
    description: 'Daftar karya berstatus Draf, Diajukan, Permintaan Revisi, dan Tervalidasi.',
    icon: Layers,
  },
  {
    id: 'std-skills',
    title: 'Radar Peta Talenta & Provenans',
    category: 'student',
    requiredRole: 'student',
    route: '/student/skills',
    description: 'Visualisasi 6 dimensi radar skill deterministik berbasis bukti nyata yang tervalidasi guru.',
    badge: 'Algoritma',
    icon: Award,
  },
  {
    id: 'std-career',
    title: 'Eksplorasi Studi & Karier',
    category: 'student',
    requiredRole: 'student',
    route: '/student/career',
    description: 'Rekomendasi jurusan dan karier masa depan dengan narasi penerjemah industri.',
    icon: Compass,
  },
  {
    id: 'std-cv',
    title: 'Digital CV & QR Otentik',
    category: 'student',
    requiredRole: 'student',
    route: '/student/cv',
    description: 'Snapshot CV SHA-256, cetak PDF resmi 2 halaman ReportLab, dan token QR verifikasi.',
    badge: 'Verifikasi',
    icon: FileCheck2,
  },

  // Guru
  {
    id: 'tch-dashboard',
    title: 'Dashboard Validasi Guru',
    category: 'teacher',
    requiredRole: 'teacher',
    route: '/teacher',
    description: 'Ringkasan antrean karya siswa yang siap ditelaah dan metrik aktivitas bimbingan.',
    icon: GraduationCap,
  },
  {
    id: 'tch-reviews',
    title: 'Antrean Validasi Portofolio',
    category: 'teacher',
    requiredRole: 'teacher',
    route: '/teacher/reviews',
    description: 'Daftar penelaahan karya siswa dari kelas bimbingan dengan opsi setujui atau minta revisi.',
    badge: 'Validasi',
    icon: CheckSquare,
  },
  {
    id: 'tch-rubric',
    title: 'Penilaian Rubrik Karakter 5 Dimensi',
    category: 'teacher',
    requiredRole: 'teacher',
    route: '/teacher/rubric',
    description: 'Skor 1–5 rubrik kanonikal: Inisiatif, Kolaborasi, Komunikasi, Tanggung Jawab, Resiliensi.',
    icon: BookOpen,
  },
  {
    id: 'tch-history',
    title: 'Riwayat Keputusan Validasi',
    category: 'teacher',
    requiredRole: 'teacher',
    route: '/teacher/history',
    description: 'Jejak rekam seluruh karya siswa yang telah divalidasi beserta catatan pembimbing.',
    icon: Layers,
  },
  {
    id: 'tch-classes',
    title: 'Kelas & Siswa Bimbingan',
    category: 'teacher',
    requiredRole: 'teacher',
    route: '/teacher/classes',
    description: 'Pemetaan rombongan belajar dan pemantauan keaktifan siswa per kelas.',
    icon: Users,
  },

  // Admin
  {
    id: 'adm-dashboard',
    title: 'Dashboard Analitik Sekolah',
    category: 'admin',
    requiredRole: 'admin',
    route: '/admin',
    description: 'Ringkasan ekosistem sekolah, total siswa aktif, kelas, dan karya tervalidasi.',
    icon: ShieldCheck,
  },
  {
    id: 'adm-heatmap',
    title: 'School Talent Heatmap Analytics',
    category: 'admin',
    requiredRole: 'admin',
    route: '/admin/heatmap',
    description: 'Peta sebaran talenta sekolah dengan threshold privasi k-anonymity (>= 5 siswa).',
    badge: 'Privasi',
    icon: BarChart3,
  },
  {
    id: 'adm-users',
    title: 'Manajemen Akun Siswa & Guru',
    category: 'admin',
    requiredRole: 'admin',
    route: '/admin/users',
    description: 'Kelola lifecycle akun (aktif/nonaktif), pembuatan akun, dan reset kredensial sekali pakai.',
    icon: Users,
  },
  {
    id: 'adm-classes',
    title: 'Manajemen Kelas & Penugasan Guru',
    category: 'admin',
    requiredRole: 'admin',
    route: '/admin/classes',
    description: 'Pengaturan rombel sekolah dan distribusi penugasan guru pembimbing kelas.',
    icon: Settings,
  },
  {
    id: 'adm-settings',
    title: 'Pengaturan Sekolah & Kebijakan Data',
    category: 'admin',
    requiredRole: 'admin',
    route: '/admin/settings',
    description: 'Konfigurasi NPSN, profil institusi, dan tata kelola privasi data sekolah.',
    icon: Settings,
  },

  // Verifikasi Publik
  {
    id: 'pub-verify-valid',
    title: 'Verifikasi Publik QR (Status Sah)',
    category: 'public',
    route: '/verify/tlnt_token_v94b8e21',
    description: 'Simulasi pemindaian QR oleh HRD / Universitas untuk membuktikan keaslian CV tanpa bocoran PII.',
    badge: 'Publik',
    icon: QrCode,
  },
  {
    id: 'pub-verify-revoked',
    title: 'Uji Verifikasi CV Dicabut (Revoked)',
    category: 'public',
    route: '/verify/demo-revoked',
    description: 'Tampilan perlindungan saat sertifikat CV telah ditarik kembali oleh pihak sekolah.',
    badge: 'Audit',
    icon: QrCode,
  },
];

export const DemoMenuModal: React.FC<DemoMenuModalProps> = ({
  isOpen,
  onClose,
  currentRole = 'student',
}) => {
  const router = useRouter();
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'student' | 'teacher' | 'admin' | 'public'>('all');
  const [isSwitching, setIsSwitching] = useState(false);

  if (!isOpen) return null;

  const handleRoleQuickSwitch = async (role: UserRole) => {
    setIsSwitching(true);
    try {
      const res = await authService.demoLogin(role);
      onClose();
      router.push(res.redirectTo);
    } catch {
      setIsSwitching(false);
    }
  };

  const handleOpenFeature = async (item: FeatureItem) => {
    setIsSwitching(true);
    try {
      if (item.requiredRole && item.requiredRole !== currentRole) {
        await authService.demoLogin(item.requiredRole);
      }
      onClose();
      router.push(item.route);
    } catch {
      setIsSwitching(false);
    }
  };

  const filteredFeatures =
    selectedCategory === 'all'
      ? DEMO_FEATURES
      : DEMO_FEATURES.filter((f) => f.category === selectedCategory);

  return (
    <div
      className="fixed inset-0 z-50 bg-[#1A0B2E]/70 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5 overflow-y-auto animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-3xl border border-[#E9E1F4] max-w-4xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden my-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Top Header */}
        <div className="bg-gradient-to-r from-[#2E1065] via-[#4C1D95] to-[#6D28D9] p-5 sm:p-6 text-white relative shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="absolute top-5 right-5 p-2 rounded-xl text-white/70 hover:text-white bg-white/10 hover:bg-white/20 transition-colors"
            aria-label="Tutup jendela demo"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#C084FC]/20 text-[#E9D5FF] border border-purple-400/30">
              <Sparkles className="w-3.5 h-3.5 text-[#C084FC]" />
              <span>EXPLORER & MENU DEMO LENGKAP</span>
            </span>
          </div>

          <h2 className="text-xl sm:text-2xl font-black tracking-tight text-white">
            Jelajah Seluruh Fitur TALENTRA.ID
          </h2>
          <p className="text-xs sm:text-sm text-[#D9CDE5] mt-1 max-w-2xl">
            Akses instan ke semua peran dan modul: mulai dari input portofolio siswa, telaah rubrik guru,
            analitik privasi admin, hingga validasi QR publik.
          </p>

          {/* Quick Role Switcher Bar */}
          <div className="mt-4 pt-4 border-t border-purple-400/20 flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-[#D9CDE5] mr-1">Masuk Cepat:</span>
            
            <button
              type="button"
              disabled={isSwitching}
              onClick={() => handleRoleQuickSwitch('student')}
              className={cn(
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all shadow-xs',
                currentRole === 'student'
                  ? 'bg-white text-[#4C1D95] ring-2 ring-[#C084FC]'
                  : 'bg-white/15 hover:bg-white/25 text-white'
              )}
            >
              <User className="w-3.5 h-3.5" />
              <span>Siswa (Alya Rahma)</span>
              {currentRole === 'student' && <CheckCircle2 className="w-3.5 h-3.5 text-[#6D28D9] ml-1" />}
            </button>

            <button
              type="button"
              disabled={isSwitching}
              onClick={() => handleRoleQuickSwitch('teacher')}
              className={cn(
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all shadow-xs',
                currentRole === 'teacher'
                  ? 'bg-white text-[#4C1D95] ring-2 ring-[#C084FC]'
                  : 'bg-white/15 hover:bg-white/25 text-white'
              )}
            >
              <GraduationCap className="w-3.5 h-3.5" />
              <span>Guru (Budi Santoso, S.Kom)</span>
              {currentRole === 'teacher' && <CheckCircle2 className="w-3.5 h-3.5 text-[#6D28D9] ml-1" />}
            </button>

            <button
              type="button"
              disabled={isSwitching}
              onClick={() => handleRoleQuickSwitch('admin')}
              className={cn(
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all shadow-xs',
                currentRole === 'admin'
                  ? 'bg-white text-[#4C1D95] ring-2 ring-[#C084FC]'
                  : 'bg-white/15 hover:bg-white/25 text-white'
              )}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Admin (Raihan Ansari)</span>
              {currentRole === 'admin' && <CheckCircle2 className="w-3.5 h-3.5 text-[#6D28D9] ml-1" />}
            </button>
          </div>
        </div>

        {/* Category Tabs */}
        <div className="px-5 sm:px-6 pt-4 pb-2 border-b border-[#E9E1F4] flex items-center gap-2 overflow-x-auto shrink-0 bg-[#FCFBFF]">
          {[
            { id: 'all', label: 'Semua Fitur (17)' },
            { id: 'student', label: 'Modul Siswa (6)' },
            { id: 'teacher', label: 'Modul Guru (5)' },
            { id: 'admin', label: 'Modul Admin (5)' },
            { id: 'public', label: 'Verifikasi Publik (2)' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setSelectedCategory(tab.id as any)}
              className={cn(
                'px-3.5 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all',
                selectedCategory === tab.id
                  ? 'bg-[#6D28D9] text-white shadow-xs'
                  : 'bg-white text-[#6F607D] hover:bg-slate-100 border border-[#E9E1F4]'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Feature Grid Content */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-3 bg-[#FCFBFF]">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {filteredFeatures.map((item) => {
              const Icon = item.icon;
              const isMatchRole = !item.requiredRole || item.requiredRole === currentRole;

              return (
                <div
                  key={item.id}
                  onClick={() => handleOpenFeature(item)}
                  className="group bg-white rounded-2xl border border-[#E9E1F4] hover:border-[#8B5CF6] p-4.5 transition-all shadow-xs hover:shadow-md cursor-pointer flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2.5">
                      <div className="w-8 h-8 rounded-xl bg-purple-50 text-[#6D28D9] group-hover:bg-[#6D28D9] group-hover:text-white transition-colors flex items-center justify-center shrink-0">
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="flex items-center gap-1.5">
                        {item.badge && (
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-extrabold uppercase bg-amber-50 text-amber-700 border border-amber-200">
                            {item.badge}
                          </span>
                        )}
                        <span
                          className={cn(
                            'px-2 py-0.5 rounded-md text-[10px] font-bold uppercase',
                            item.category === 'student' && 'bg-blue-50 text-blue-700',
                            item.category === 'teacher' && 'bg-emerald-50 text-emerald-700',
                            item.category === 'admin' && 'bg-purple-50 text-purple-700',
                            item.category === 'public' && 'bg-slate-100 text-slate-700'
                          )}
                        >
                          {item.category}
                        </span>
                      </div>
                    </div>

                    <h3 className="text-sm font-extrabold text-[#261331] group-hover:text-[#6D28D9] transition-colors leading-snug">
                      {item.title}
                    </h3>
                    <p className="text-xs text-[#6F607D] mt-1.5 leading-relaxed line-clamp-2">
                      {item.description}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-[#6D28D9]">
                    <span className="text-[11px] text-[#9584A7] font-medium">
                      {isMatchRole ? 'Siap dibuka' : `Akan beralih ke ${item.requiredRole}`}
                    </span>
                    <span className="inline-flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                      <span>Buka</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Modal Footer Note */}
        <div className="p-4 px-6 bg-white border-t border-[#E9E1F4] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#6F607D] shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Mode Demo Terintegrasi — Data tervalidasi dapat dicoba bebas di browser.</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-[#261331] font-bold text-xs transition-colors"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
};
