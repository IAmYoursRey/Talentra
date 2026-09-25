'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '../../../../components/layout/AppShell';
import { TagSelector } from '../../../../components/student/TagSelector';
import { MockFileUploader } from '../../../../components/student/MockFileUploader';
import { portfolioService } from '../../../../services/portfolio.service';
import { authService } from '../../../../services/auth.service';
import { ActivityType, CanonicalTag, EvidenceSource } from '../../../../types/portfolio.types';
import {
  ArrowLeft,
  Save,
  Send,
  Link as LinkIcon,
  Upload,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import Link from 'next/link';

export default function NewPortfolioPage() {
  const router = useRouter();

  // Form Fields
  const [title, setTitle] = useState('');
  const [activityType, setActivityType] = useState<ActivityType>('project');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [description, setDescription] = useState('');
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<CanonicalTag[]>([]);

  // Evidence Source: File vs Link
  const [evidenceMode, setEvidenceMode] = useState<'file' | 'link'>('file');
  const [fileEvidence, setFileEvidence] = useState<EvidenceSource | null>(null);
  const [linkUrl, setLinkUrl] = useState('');

  // Status & Feedback
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successBanner, setSuccessBanner] = useState('');

  useEffect(() => {
    portfolioService.getCanonicalTags().then(setAvailableTags);
  }, []);

  const handleSave = async (isDraft: boolean) => {
    setErrorMsg('');

    // Validations
    if (!title.trim()) {
      setErrorMsg('Judul karya wajib diisi.');
      return;
    }
    if (!description.trim()) {
      setErrorMsg('Deskripsi karya wajib diisi.');
      return;
    }
    if (selectedTagIds.length < 3 || selectedTagIds.length > 5) {
      setErrorMsg('Anda wajib memilih minimal 3 dan maksimal 5 tag kapabilitas/keahlian.');
      return;
    }

    let resolvedEvidence: EvidenceSource;
    if (evidenceMode === 'file') {
      if (!fileEvidence && !isDraft) {
        setErrorMsg('Silakan unggah dokumen atau simulasikan berkas bukti karya.');
        return;
      }
      resolvedEvidence = fileEvidence || {
        type: 'file',
        url: '/mock-uploads/Dokumen_Default.pdf',
        fileName: 'Draft_Lampiran_Karya.pdf',
        fileSize: '1.2 MB',
        mimeType: 'application/pdf',
      };
    } else {
      if (!linkUrl.trim() && !isDraft) {
        setErrorMsg('Tautan eksternal (GitHub/Google Drive/URL) wajib diisi.');
        return;
      }
      resolvedEvidence = {
        type: 'link',
        url: linkUrl || 'https://github.com/student-demo/portfolio-project',
        platform: linkUrl.includes('github') ? 'github' : linkUrl.includes('drive') ? 'drive' : 'web',
      };
    }

    setIsSubmitting(true);

    try {
      const session = await authService.getCurrentSession();
      const currentUser = session.user;

      const created = await portfolioService.createPortfolioItem({
        title,
        activityType,
        date,
        description,
        tags: selectedTagIds,
        evidence: resolvedEvidence,
        status: isDraft ? 'draft' : 'submitted',
        studentId: currentUser?.id || 'usr_std_001',
        studentName: currentUser?.name || 'Alya Rahma Azzahra',
        studentClass: currentUser?.className || 'XII RPL 1',
      });

      setSuccessBanner(
        isDraft
          ? 'Draf portofolio berhasil disimpan.'
          : 'Portofolio berhasil diajukan! Bukti karya telah masuk ke antrean validasi guru.'
      );

      setTimeout(() => {
        router.push(`/student/portfolio/${created.id}`);
      }, 1200);
    } catch (err: any) {
      setErrorMsg(err.message || 'Gagal menyimpan karya.');
      setIsSubmitting(false);
    }
  };

  return (
    <AppShell pageTitle="Tambah Portofolio Karya" expectedRole="student">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Back link */}
        <div className="flex items-center justify-between">
          <Link
            href="/student/portfolio"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Kembali ke Portofolio</span>
          </Link>
          <span className="text-xs text-slate-400">Tahap 1 / Formulir Pengajuan Bukti Karya</span>
        </div>

        {/* Page Title & Instructions */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            Pengajuan Bukti Karya Nyata (Proof of Work)
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 mt-1 leading-relaxed">
            Isi informasi karya dengan jelas dan lampirkan bukti autentik. Karya yang disetujui oleh guru pembimbing akan secara otomatis membentuk visualisasi radar kompetensi dan Digital CV Anda.
          </p>
        </div>

        {/* Error / Success Notifications */}
        {errorMsg && (
          <div className="p-4 rounded-xl bg-reject-50 border border-reject-200 flex items-start gap-3 text-reject-800 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0 text-reject-600 mt-0.5" />
            <div>
              <p className="font-bold">Periksa Kembali Data Anda:</p>
              <p className="mt-0.5">{errorMsg}</p>
            </div>
          </div>
        )}

        {successBanner && (
          <div className="p-4 rounded-xl bg-endorse-50 border border-endorse-300 flex items-center gap-3 text-endorse-800 text-xs">
            <CheckCircle2 className="w-5 h-5 shrink-0 text-endorse-600" />
            <p className="font-semibold text-sm">{successBanner}</p>
          </div>
        )}

        {/* Main Progressive Form Card */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-xs space-y-8">
          {/* Section 1: Informasi Utama */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider pb-2 border-b border-slate-100">
              1. Informasi Karya
            </h3>

            <div>
              <label htmlFor="title" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Judul Karya / Proyek <span className="text-reject-500">*</span>
              </label>
              <input
                id="title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Contoh: Aplikasi Monitoring Kehadiran Kelas dengan QR Dinamis"
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="activityType" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Jenis Kegiatan <span className="text-reject-500">*</span>
                </label>
                <select
                  id="activityType"
                  value={activityType}
                  onChange={(e) => setActivityType(e.target.value as ActivityType)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
                >
                  <option value="project">Proyek Pembelajaran / Aplikasi</option>
                  <option value="competition">Lomba / Kejuaraan / Kompetisi</option>
                  <option value="organization">Organisasi / Kepanitiaan OSIS</option>
                  <option value="certification">Sertifikasi & Pelatihan</option>
                  <option value="research">Karya Ilmiah / Riset</option>
                  <option value="volunteering">Kegiatan Sosial / Pengabdian</option>
                </select>
              </div>

              <div>
                <label htmlFor="date" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Tanggal Pelaksanaan / Selesai <span className="text-reject-500">*</span>
                </label>
                <input
                  id="date"
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label htmlFor="description" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Deskripsi Karya & Peran Anda <span className="text-reject-500">*</span>
              </label>
              <textarea
                id="description"
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Ceritakan latar belakang karya, tujuan, peran Anda secara spesifik, serta dampak atau hasil yang diperoleh..."
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Jelaskan peran nyata Anda (misal: penanggung jawab frontend, perancang desain, pemakalah) tanpa melebih-lebihkan fakta.
              </p>
            </div>
          </div>

          {/* Section 2: Capability Tagging (Strict 3 to 5 rule) */}
          <div className="space-y-4 pt-4 border-t border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider pb-2 border-b border-slate-100">
              2. Pemilihan Tag Kapabilitas & Kompetensi
            </h3>

            <TagSelector
              availableTags={availableTags}
              selectedTagIds={selectedTagIds}
              onChange={setSelectedTagIds}
              minTags={3}
              maxTags={5}
            />
          </div>

          {/* Section 3: Evidence Source */}
          <div className="space-y-4 pt-4 border-t border-slate-100">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                3. Sumber Bukti Autentik (Evidence Source)
              </h3>
              <div className="flex items-center border border-slate-200 rounded-lg p-0.5 bg-slate-50">
                <button
                  type="button"
                  onClick={() => setEvidenceMode('file')}
                  className={`px-3 py-1 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                    evidenceMode === 'file' ? 'bg-white shadow-2xs text-brand-600' : 'text-slate-600'
                  }`}
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>Unggah Berkas</span>
                </button>
                <button
                  type="button"
                  onClick={() => setEvidenceMode('link')}
                  className={`px-3 py-1 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                    evidenceMode === 'link' ? 'bg-white shadow-2xs text-brand-600' : 'text-slate-600'
                  }`}
                >
                  <LinkIcon className="w-3.5 h-3.5" />
                  <span>Tautan Link</span>
                </button>
              </div>
            </div>

            {evidenceMode === 'file' ? (
              <MockFileUploader
                onFileSelect={setFileEvidence}
                selectedEvidence={fileEvidence}
              />
            ) : (
              <div className="space-y-2">
                <label htmlFor="linkUrl" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Tautan Repositori / Berkas Cloud (GitHub, Drive, URL)
                </label>
                <input
                  id="linkUrl"
                  type="url"
                  value={linkUrl}
                  onChange={(e) => setLinkUrl(e.target.value)}
                  placeholder="https://github.com/username/project-name atau https://drive.google.com/..."
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
                />
                <p className="text-[11px] text-slate-400">
                  Pastikan tautan dapat dibuka (public/accessible) oleh tim guru validator sekolah.
                </p>
              </div>
            )}
          </div>

          {/* Form Actions Buttons */}
          <div className="pt-6 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-end gap-3">
            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => handleSave(true)}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-sm transition-colors shadow-2xs focus:ring-2 focus:ring-slate-300"
            >
              <Save className="w-4 h-4 text-slate-500" />
              <span>Simpan Draft</span>
            </button>

            <button
              type="button"
              disabled={isSubmitting}
              onClick={() => handleSave(false)}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-sm transition-colors shadow-xs focus:ring-2 focus:ring-brand-500 focus:ring-offset-1 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              <span>{isSubmitting ? 'Memproses...' : 'Kirim untuk Validasi'}</span>
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
