'use client';

import React, { useState } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import {
  School,
  Lock,
  Database,
  FileCheck2,
  Edit,
  RotateCcw,
  X,
  ShieldCheck,
  Save,
  CheckCircle2,
  HardDrive,
  KeyRound,
  Sliders,
} from 'lucide-react';
import {
  settingsService,
  AllSchoolSettings,
} from '../../../services/settings.service';

type ActiveModal = 'identity' | 'security' | 'storage' | 'cv' | null;

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<AllSchoolSettings>(() =>
    settingsService.getCachedSettings()
  );
  const [activeModal, setActiveModal] = useState<ActiveModal>(null);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'info'; text: string } | null>(null);
  const [isResetConfirmOpen, setIsResetConfirmOpen] = useState(false);

  // Form states for modals
  const [identityForm, setIdentityForm] = useState(settings.identity);
  const [securityForm, setSecurityForm] = useState(settings.security);
  const [storageForm, setStorageForm] = useState(settings.storage);
  const [cvForm, setCvForm] = useState(settings.cvPolicy);

  // Re-sync form when modal opens
  const openModal = (modal: ActiveModal) => {
    if (modal === 'identity') setIdentityForm({ ...settings.identity });
    if (modal === 'security') setSecurityForm({ ...settings.security });
    if (modal === 'storage') setStorageForm({ ...settings.storage });
    if (modal === 'cv') setCvForm({ ...settings.cvPolicy });
    setActiveModal(modal);
  };

  const showFeedback = (text: string, type: 'success' | 'info' = 'success') => {
    setFeedbackMsg({ text, type });
    setTimeout(() => setFeedbackMsg(null), 4000);
  };

  const handleSaveIdentity = async (e: React.FormEvent) => {
    e.preventDefault();
    const updated = await settingsService.updateSettings({ identity: identityForm });
    setSettings(updated);
    setActiveModal(null);
    showFeedback('Identitas sekolah dan periode akademik berhasil diperbarui.');
  };

  const handleSaveSecurity = async (e: React.FormEvent) => {
    e.preventDefault();
    const updated = await settingsService.updateSettings({ security: securityForm });
    setSettings(updated);
    setActiveModal(null);
    showFeedback('Kebijakan keamanan institusi dan sesi otentikasi berhasil disimpan.');
  };

  const handleSaveStorage = async (e: React.FormEvent) => {
    e.preventDefault();
    const updated = await settingsService.updateSettings({ storage: storageForm });
    setSettings(updated);
    setActiveModal(null);
    showFeedback('Konfigurasi storage, format file, dan batas kuota berhasil diterapkan.');
  };

  const handleSaveCvPolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    const updated = await settingsService.updateSettings({ cvPolicy: cvForm });
    setSettings(updated);
    setActiveModal(null);
    showFeedback('Kebijakan penerbitan Digital CV dan QR verifikasi publik berhasil diperbarui.');
  };

  const handleResetDefaults = async () => {
    const res = await settingsService.resetToDefault();
    setSettings(res);
    setIsResetConfirmOpen(false);
    showFeedback('Semua pengaturan sekolah dikembalikan ke standar awal.', 'info');
  };

  return (
    <AppShell pageTitle="School Settings" expectedRole="admin" isPageLoading={false}>
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              School Settings
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Konfigurasi institusi, keamanan otentikasi, kuota penyimpanan, dan kebijakan Digital CV.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsResetConfirmOpen(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-slate-200 bg-white text-xs font-bold text-slate-600 hover:text-slate-900 hover:border-slate-300 transition-all shadow-xs"
              title="Reset ke pengaturan bawaan"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Default</span>
            </button>
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#F3E8FF] border border-purple-200 text-[#6D28D9] font-bold text-xs shadow-xs">
              <span>{settings.identity.academicYear} • {settings.identity.semester.split(' ')[0]}</span>
            </div>
          </div>
        </div>

        {/* Feedback alert */}
        {feedbackMsg && (
          <div
            className={`p-4 rounded-xl border text-xs font-bold flex items-center justify-between animate-in fade-in ${
              feedbackMsg.type === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-purple-50 border-purple-200 text-purple-800'
            }`}
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{feedbackMsg.text}</span>
            </div>
            <button
              type="button"
              onClick={() => setFeedbackMsg(null)}
              className="text-slate-400 hover:text-slate-700"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* 4 Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card 1: Identitas Sekolah */}
          <div className="bg-white rounded-[22px] border border-[#E9E1F4] p-6 sm:p-7 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between hover:border-purple-200 transition-all">
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-purple-100 text-[#6D28D9] flex items-center justify-center shadow-xs">
                    <School className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-extrabold text-[#261331]">Identitas Sekolah</h2>
                    <p className="text-[11px] text-[#6F607D]">Data resmi lembaga dan periode belajar aktif</p>
                  </div>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Aktif
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Nama Sekolah:</span>
                  <span className="font-bold text-[#261331]">{settings.identity.schoolName}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">NPSN:</span>
                  <span className="font-mono font-bold text-[#261331]">{settings.identity.npsn}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Tahun Akademik:</span>
                  <span className="font-bold text-[#261331]">{settings.identity.academicYear}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Semester Aktif:</span>
                  <span className="font-bold text-[#6D28D9]">{settings.identity.semester}</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="font-semibold text-[#6F607D]">Kepala Sekolah:</span>
                  <span className="font-bold text-[#261331]">{settings.identity.principalName}</span>
                </div>
              </div>
            </div>

            <div className="pt-6 border-t border-[#E9E1F4] mt-5 flex items-center justify-between">
              <span className="text-[10px] text-slate-400">Tersimpan di lokal & cloud</span>
              <button
                type="button"
                onClick={() => openModal('identity')}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl tal-btn-primary font-bold text-xs shadow-md"
              >
                <Edit className="w-3.5 h-3.5" />
                <span>Edit Identitas</span>
              </button>
            </div>
          </div>

          {/* Card 2: Keamanan */}
          <div className="bg-white rounded-[22px] border border-[#E9E1F4] p-6 sm:p-7 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between hover:border-purple-200 transition-all">
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-purple-100 text-[#6D28D9] flex items-center justify-center shadow-xs">
                    <Lock className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-extrabold text-[#261331]">Keamanan & Otentikasi</h2>
                    <p className="text-[11px] text-[#6F607D]">Sesi otentikasi, proteksi cookie, dan RBAC</p>
                  </div>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-[#6D28D9] border border-purple-200">
                  Terkunci
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Akses Cepat Akun Demo:</span>
                  <span className={`px-2 py-0.5 rounded-md font-bold text-[11px] ${settings.security.demoLogin ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>
                    {settings.security.demoLogin ? 'AKTIF (ON)' : 'NONAKTIF'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Proteksi Secure Cookie:</span>
                  <span className="font-bold text-emerald-700">{settings.security.secureCookie} (SameSite=Lax)</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Mode Otorisasi RBAC:</span>
                  <span className="font-mono font-bold text-[#6D28D9]">{settings.security.rbacMode}</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="font-semibold text-[#6F607D]">Batas Waktu Sesi (TTL):</span>
                  <span className="font-bold text-[#261331]">{settings.security.sessionTimeoutHours} Jam</span>
                </div>
              </div>
            </div>

            <div className="pt-6 border-t border-[#E9E1F4] mt-5 flex items-center justify-between">
              <span className="text-[10px] text-slate-400">HMAC-SHA256 Protected</span>
              <button
                type="button"
                onClick={() => openModal('security')}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl tal-btn-primary font-bold text-xs shadow-md"
              >
                <KeyRound className="w-3.5 h-3.5" />
                <span>Security Policy</span>
              </button>
            </div>
          </div>

          {/* Card 3: Storage & Upload */}
          <div className="bg-white rounded-[22px] border border-[#E9E1F4] p-6 sm:p-7 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between hover:border-purple-200 transition-all">
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-purple-100 text-[#6D28D9] flex items-center justify-center shadow-xs">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-extrabold text-[#261331]">Storage & Kuota Upload</h2>
                    <p className="text-[11px] text-[#6F607D]">Penyimpanan bukti karya dan batas berkas</p>
                  </div>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                  Cloud Object
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Mode Penyimpanan:</span>
                  <span className="font-bold text-[#261331]">{settings.storage.freeTier === 'ON' ? 'Cloudflare R2 (Free Tier)' : 'Dedicated S3'}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Private File Isolation:</span>
                  <span className="font-bold text-emerald-700">{settings.storage.privateFiles} (Presigned URL)</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Batas Ukuran per Berkas:</span>
                  <span className="font-bold text-[#261331]">{settings.storage.maxFileSizeMb} MB</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="font-semibold text-[#6F607D]">Format Diizinkan:</span>
                  <span className="font-mono font-bold text-[#6D28D9]">{settings.storage.allowedFormats.join(', ')}</span>
                </div>
              </div>
            </div>

            <div className="pt-6 border-t border-[#E9E1F4] mt-5 flex items-center justify-between">
              <span className="text-[10px] text-slate-400">Zero Public Bucket Leak</span>
              <button
                type="button"
                onClick={() => openModal('storage')}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl tal-btn-primary font-bold text-xs shadow-md"
              >
                <HardDrive className="w-3.5 h-3.5" />
                <span>Atur Kuota</span>
              </button>
            </div>
          </div>

          {/* Card 4: CV & Verification */}
          <div className="bg-white rounded-[22px] border border-[#E9E1F4] p-6 sm:p-7 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between hover:border-purple-200 transition-all">
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-purple-100 text-[#6D28D9] flex items-center justify-center shadow-xs">
                    <FileCheck2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-extrabold text-[#261331]">Kebijakan Digital CV</h2>
                    <p className="text-[11px] text-[#6F607D]">Aturan seleksi bukti, QR, dan pencabutan</p>
                  </div>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Terstandar
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Maks. Portofolio Terpilih:</span>
                  <span className="font-bold text-[#6D28D9]">{settings.cvPolicy.evidenceMax} Karya (Batas 1–8)</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">QR Verifikasi Publik:</span>
                  <span className="font-bold text-emerald-700">{settings.cvPolicy.qrVerification} (Aktif)</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Wajib ACC Guru Pembimbing:</span>
                  <span className="font-bold text-[#261331]">
                    {settings.cvPolicy.requireTeacherApproval ? 'YA (Enforced)' : 'OPSIONAL'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="font-semibold text-[#6F607D]">Kebijakan Revokasi Dokumen:</span>
                  <span className="font-bold text-rose-600">{settings.cvPolicy.revocationMode}</span>
                </div>
              </div>
            </div>

            <div className="pt-6 border-t border-[#E9E1F4] mt-5 flex items-center justify-between">
              <span className="text-[10px] text-slate-400">Preserving Proof of Work</span>
              <button
                type="button"
                onClick={() => openModal('cv')}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl tal-btn-primary font-bold text-xs shadow-md"
              >
                <Sliders className="w-3.5 h-3.5" />
                <span>Atur Kebijakan</span>
              </button>
            </div>
          </div>
        </div>

        {/* Footer info notice */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 flex items-center gap-3">
          <ShieldCheck className="w-5 h-5 text-[#6D28D9] shrink-0" />
          <p className="text-xs text-[#6F607D]">
            Seluruh konfigurasi tersimpan secara persisten dan terlindungi di level otorisasi server. Hanya admin sekolah bersertifikat yang dapat memodifikasi parameter institusi.
          </p>
        </div>
      </div>

      {/* ================= MODAL 1: EDIT IDENTITAS SEKOLAH ================= */}
      {activeModal === 'identity' && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-7 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <School className="w-5 h-5 text-[#6D28D9]" />
                <h3 className="font-extrabold text-slate-900 text-base">Edit Identitas Sekolah</h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveIdentity} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Nama Sekolah / Instansi:</label>
                <input
                  type="text"
                  required
                  value={identityForm.schoolName}
                  onChange={(e) => setIdentityForm({ ...identityForm, schoolName: e.target.value })}
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">NPSN:</label>
                  <input
                    type="text"
                    required
                    value={identityForm.npsn}
                    onChange={(e) => setIdentityForm({ ...identityForm, npsn: e.target.value })}
                    className="w-full p-2.5 border border-slate-200 rounded-xl text-xs font-mono text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Provinsi:</label>
                  <input
                    type="text"
                    required
                    value={identityForm.province}
                    onChange={(e) => setIdentityForm({ ...identityForm, province: e.target.value })}
                    className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Tahun Akademik:</label>
                  <input
                    type="text"
                    required
                    value={identityForm.academicYear}
                    onChange={(e) => setIdentityForm({ ...identityForm, academicYear: e.target.value })}
                    className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                    placeholder="Contoh: 2026 / 2027"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Semester Aktif:</label>
                  <select
                    value={identityForm.semester}
                    onChange={(e) => setIdentityForm({ ...identityForm, semester: e.target.value })}
                    className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                  >
                    <option value="Semester 1 (Ganjil)">Semester 1 (Ganjil)</option>
                    <option value="Semester 2 (Genap)">Semester 2 (Genap)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Nama Kepala Sekolah / Pejabat:</label>
                <input
                  type="text"
                  required
                  value={identityForm.principalName}
                  onChange={(e) => setIdentityForm({ ...identityForm, principalName: e.target.value })}
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                />
              </div>

              <div className="pt-4 flex items-center justify-end gap-2.5 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl tal-btn-primary text-xs font-bold shadow-md"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>Simpan Perubahan</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================= MODAL 2: KEAMANAN & OTENTIKASI ================= */}
      {activeModal === 'security' && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-7 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <Lock className="w-5 h-5 text-[#6D28D9]" />
                <h3 className="font-extrabold text-slate-900 text-base">Pengaturan Keamanan & Sesi</h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveSecurity} className="mt-5 space-y-4">
              <div className="p-3.5 rounded-xl bg-purple-50/70 border border-purple-100 flex items-center justify-between">
                <div>
                  <span className="block text-xs font-bold text-[#261331]">Fitur Masuk Akun Demo (Header Pill)</span>
                  <span className="text-[11px] text-[#6F607D]">Izinkan pengujian cepat peran siswa, guru, admin</span>
                </div>
                <input
                  type="checkbox"
                  checked={securityForm.demoLogin}
                  onChange={(e) => setSecurityForm({ ...securityForm, demoLogin: e.target.checked })}
                  className="w-5 h-5 accent-[#6D28D9] rounded cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Proteksi Cookie Sesi:</label>
                <select
                  value={securityForm.secureCookie}
                  onChange={(e) => setSecurityForm({ ...securityForm, secureCookie: e.target.value })}
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                >
                  <option value="ON">ON (HttpOnly, SameSite=Lax, Secure)</option>
                  <option value="STRICT">STRICT (SameSite=Strict, High Privacy)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Enforcement Model RBAC:</label>
                <select
                  value={securityForm.rbacMode}
                  onChange={(e) => setSecurityForm({ ...securityForm, rbacMode: e.target.value })}
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                >
                  <option value="STRICT">STRICT (Otorisasi Server Penuh, Tolak Mutasi Klien)</option>
                  <option value="STANDARD">STANDARD (Verifikasi Multi-Peran Standar)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Batas Masa Berlaku Sesi (Jam):</label>
                <input
                  type="number"
                  min={1}
                  max={168}
                  value={securityForm.sessionTimeoutHours}
                  onChange={(e) =>
                    setSecurityForm({ ...securityForm, sessionTimeoutHours: parseInt(e.target.value) || 24 })
                  }
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                />
              </div>

              <div className="pt-4 flex items-center justify-end gap-2.5 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl tal-btn-primary text-xs font-bold shadow-md"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>Terapkan Kebijakan</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================= MODAL 3: STORAGE & KUOTA ================= */}
      {activeModal === 'storage' && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-7 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <Database className="w-5 h-5 text-[#6D28D9]" />
                <h3 className="font-extrabold text-slate-900 text-base">Atur Kuota & Objek Penyimpanan</h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveStorage} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Penyedia Object Storage:</label>
                <select
                  value={storageForm.freeTier}
                  onChange={(e) => setStorageForm({ ...storageForm, freeTier: e.target.value })}
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                >
                  <option value="ON">Cloudflare R2 Free-Tier (10 GB gratis, 0 biaya egress)</option>
                  <option value="OFF">Dedicated AWS S3 Standard</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Maksimum Ukuran Berkas per Karya (MB):</label>
                <input
                  type="number"
                  min={5}
                  max={100}
                  value={storageForm.maxFileSizeMb}
                  onChange={(e) =>
                    setStorageForm({ ...storageForm, maxFileSizeMb: parseInt(e.target.value) || 25 })
                  }
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Ambang Peringatan Kuota (Soft Limit):</label>
                <select
                  value={storageForm.softLimitThreshold}
                  onChange={(e) => setStorageForm({ ...storageForm, softLimitThreshold: e.target.value })}
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                >
                  <option value="75%">75% Terisi (Pemberitahuan Dini)</option>
                  <option value="80%">80% Terisi (Rekomendasi Default)</option>
                  <option value="90%">90% Terisi (Kritis)</option>
                </select>
              </div>

              <div className="pt-4 flex items-center justify-end gap-2.5 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl tal-btn-primary text-xs font-bold shadow-md"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>Simpan Kuota</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================= MODAL 4: ATUR KEBIJAKAN CV ================= */}
      {activeModal === 'cv' && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-7 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <FileCheck2 className="w-5 h-5 text-[#6D28D9]" />
                <h3 className="font-extrabold text-slate-900 text-base">Kebijakan Digital CV & Verifikasi</h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveModal(null)}
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveCvPolicy} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Maksimum Karya Terpilih dalam CV (1–8 buah):
                </label>
                <input
                  type="number"
                  min={1}
                  max={8}
                  value={cvForm.evidenceMax}
                  onChange={(e) =>
                    setCvForm({ ...cvForm, evidenceMax: Math.min(8, Math.max(1, parseInt(e.target.value) || 8)) })
                  }
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">
                  Sesuai kebijakan integritas: hanya 1 s.d. 8 karya tervalidasi yang dapat dipilih.
                </span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Status QR Verifikasi Publik:</label>
                <select
                  value={cvForm.qrVerification}
                  onChange={(e) => setCvForm({ ...cvForm, qrVerification: e.target.value })}
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                >
                  <option value="ON">ON (QR Code Terenkripsi Otomatis Diterbitkan)</option>
                  <option value="OFF">OFF (Verifikasi Manual Saja)</option>
                </select>
              </div>

              <div className="p-3.5 rounded-xl bg-purple-50/70 border border-purple-100 flex items-center justify-between">
                <div>
                  <span className="block text-xs font-bold text-[#261331]">Wajib ACC Guru Pembimbing</span>
                  <span className="text-[11px] text-[#6F607D]">Hanya karya berstatus Disetujui yang dapat masuk CV</span>
                </div>
                <input
                  type="checkbox"
                  checked={cvForm.requireTeacherApproval}
                  onChange={(e) => setCvForm({ ...cvForm, requireTeacherApproval: e.target.checked })}
                  className="w-5 h-5 accent-[#6D28D9] rounded cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Kebijakan Pencabutan / Revokasi:</label>
                <select
                  value={cvForm.revocationMode}
                  onChange={(e) => setCvForm({ ...cvForm, revocationMode: e.target.value })}
                  className="w-full p-2.5 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                >
                  <option value="Immediate">Immediate (Seketika Revoked saat Siswa / Admin Cabut)</option>
                  <option value="Review">Review (Memerlukan Persetujuan Kepala Sekolah)</option>
                </select>
              </div>

              <div className="pt-4 flex items-center justify-end gap-2.5 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActiveModal(null)}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl tal-btn-primary text-xs font-bold shadow-md"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>Simpan Kebijakan CV</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================= MODAL: KONFIRMASI RESET ================= */}
      {isResetConfirmOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95 space-y-4">
            <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center mx-auto">
              <RotateCcw className="w-6 h-6" />
            </div>
            <div className="text-center">
              <h3 className="text-base font-extrabold text-slate-900">Kembalikan ke Default?</h3>
              <p className="text-xs text-slate-500 mt-1">
                Semua nilai pengaturan sekolah akan dikembalikan ke konfigurasi standar awal.
              </p>
            </div>
            <div className="flex items-center gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsResetConfirmOpen(false)}
                className="flex-1 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50"
              >
                Batal
              </button>
              <button
                type="button"
                onClick={handleResetDefaults}
                className="flex-1 py-2 rounded-xl tal-btn-primary text-xs font-bold shadow-md"
              >
                Ya, Reset
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
