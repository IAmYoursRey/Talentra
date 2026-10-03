'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { AppShell } from '../../../../components/layout/AppShell';
import { StatusBadge } from '../../../../components/common/StatusBadge';
import { TagChip } from '../../../../components/common/TagChip';
import { EvidencePreview } from '../../../../components/common/EvidencePreview';
import { ValidationTimeline } from '../../../../components/common/ValidationTimeline';
import { LoadingSkeleton } from '../../../../components/common/LoadingSkeleton';
import { ErrorState } from '../../../../components/common/ErrorState';
import { portfolioService } from '../../../../services/portfolio.service';
import { PortfolioItem } from '../../../../types/portfolio.types';
import {
  ArrowLeft,
  Calendar,
  Layers,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  FileEdit,
  Send,
} from 'lucide-react';
import Link from 'next/link';

export default function StudentPortfolioDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [item, setItem] = useState<PortfolioItem | null>(() => {
    return portfolioService.getCachedItems().find((p) => p.id === id) || null;
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Revision resubmit inline state
  const [isEditingRevision, setIsEditingRevision] = useState(false);
  const [revisedDescription, setRevisedDescription] = useState(() => {
    return portfolioService.getCachedItems().find((p) => p.id === id)?.description || '';
  });
  const [isResubmitting, setIsResubmitting] = useState(false);
  const [resubmitSuccess, setResubmitSuccess] = useState(false);

  const fetchDetail = async () => {
    if (!id) return;
    const data = await portfolioService.getPortfolioItemById(id);
    if (!data && !item) {
      setErrorMsg('Portofolio karya tidak ditemukan.');
    } else if (data) {
      setItem(data);
      setRevisedDescription(data.description);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

  const handleResubmitRevision = async () => {
    if (!item) return;
    setIsResubmitting(true);
    try {
      const updated = await portfolioService.resubmitRevision(item.id, {
        description: revisedDescription,
      });
      setItem(updated);
      setIsEditingRevision(false);
      setResubmitSuccess(true);
      setTimeout(() => setResubmitSuccess(false), 3000);
    } catch (err: any) {
      alert(err.message || 'Gagal mengajukan perbaikan portofolio.');
    } finally {
      setIsResubmitting(false);
    }
  };

  return (
    <AppShell pageTitle="Detail Portofolio" expectedRole="student" isPageLoading={isLoading}>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Navigation bar */}
        <div className="flex items-center justify-between">
          <Link
            href="/student/portfolio"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Kembali ke Portofolio</span>
          </Link>
          {item && <span className="text-xs text-slate-400 font-mono">ID: {item.id}</span>}
        </div>

        {isLoading ? (
          <div className="bg-white p-8 rounded-2xl border border-slate-200">
            <LoadingSkeleton rows={5} />
          </div>
        ) : errorMsg || !item ? (
          <ErrorState
            title="Karya Tidak Ditemukan"
            message={errorMsg || 'Data karya ini mungkin telah dihapus atau dipindahkan.'}
            onRetry={fetchDetail}
          />
        ) : (
          <div className="space-y-6">
            {/* Main Header Card */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-xs space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <StatusBadge status={item.status} size="lg" />
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Dibuat: {item.date}</span>
                </div>
              </div>

              <h2 className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight leading-tight">
                {item.title}
              </h2>

              <div className="flex items-center gap-2 pt-1 flex-wrap">
                <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 capitalize flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5" />
                  <span>Kategori: {item.activityType}</span>
                </span>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-xs text-slate-600">Siswa: {item.studentName} ({item.studentClass})</span>
              </div>
            </div>

            {/* Revision Requested Notice & CTA */}
            {item.status === 'revision_requested' && (
              <div className="p-5 sm:p-6 rounded-2xl border-2 border-revision-400 bg-revision-50 shadow-xs space-y-4">
                <div className="flex items-start gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-revision-100 text-revision-700 flex items-center justify-center shrink-0 border border-revision-300">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-revision-900">
                      Catatan Perbaikan dari Guru Pembimbing
                    </h3>
                    <p className="text-xs sm:text-sm text-revision-900 mt-1.5 leading-relaxed bg-white/70 p-3 rounded-xl border border-revision-200">
                      &ldquo;{item.teacherFeedback || 'Mohon lengkapi berkas karya atau perbaiki deskripsi.'}&rdquo;
                    </p>
                  </div>
                </div>

                {isEditingRevision ? (
                  <div className="p-4 bg-white rounded-xl border border-revision-200 space-y-3">
                    <label className="block text-xs font-bold text-slate-700 uppercase">
                      Pembaruan Deskripsi / Bukti Tanggapan Revisi:
                    </label>
                    <textarea
                      rows={3}
                      value={revisedDescription}
                      onChange={(e) => setRevisedDescription(e.target.value)}
                      className="w-full p-3 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-revision-500"
                    />
                    <div className="flex items-center justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => setIsEditingRevision(false)}
                        className="px-3.5 py-1.5 rounded-xl tal-btn-secondary text-xs font-bold"
                      >
                        Batal
                      </button>
                      <button
                        type="button"
                        disabled={isResubmitting}
                        onClick={handleResubmitRevision}
                        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl tal-btn-amber font-bold text-xs disabled:opacity-50"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>{isResubmitting ? 'Mengirim...' : 'Kirim Ulang ke Guru'}</span>
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={() => setIsEditingRevision(true)}
                      className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl tal-btn-amber font-bold text-xs"
                    >
                      <RotateCcw className="w-4 h-4" />
                      <span>Perbaiki & Kirim Ulang</span>
                    </button>
                  </div>
                )}
              </div>
            )}

            {resubmitSuccess && (
              <div className="p-4 rounded-xl bg-endorse-50 border border-endorse-300 text-endorse-800 text-xs flex items-center gap-2 font-medium">
                <CheckCircle2 className="w-4 h-4 text-endorse-600" />
                <span>Perbaikan berhasil diajukan ulang ke antrean guru validator!</span>
              </div>
            )}

            {/* Two Column: Left Info & Evidence, Right Timeline */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column (2 spans) */}
              <div className="lg:col-span-2 space-y-6">
                {/* Description Card */}
                <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-3">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Deskripsi Karya & Peran
                  </h3>
                  <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                    {item.description}
                  </p>
                </div>

                {/* Evidence Source Card */}
                <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-3">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Sumber Bukti Karya (Evidence)
                  </h3>
                  <EvidencePreview evidence={item.evidence} />
                </div>

                {/* Capability Tags */}
                <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-3">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Tag Kompetensi Terdaftar ({item.tags.length})
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {item.tags.map((t) => (
                      <TagChip key={t} label={t} />
                    ))}
                  </div>
                </div>
              </div>

              {/* Right Column: Validation Timeline */}
              <div className="space-y-6">
                <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider pb-2 border-b border-slate-100">
                    Riwayat Validasi (Timeline)
                  </h3>
                  <ValidationTimeline events={item.timeline} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
