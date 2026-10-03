'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { AppShell } from '../../../../components/layout/AppShell';
import { StatusBadge } from '../../../../components/common/StatusBadge';
import { TagChip } from '../../../../components/common/TagChip';
import { EvidencePreview } from '../../../../components/common/EvidencePreview';
import { ValidationTimeline } from '../../../../components/common/ValidationTimeline';
import { SoftSkillRubricForm } from '../../../../components/teacher/SoftSkillRubricForm';
import { ConfirmDialog } from '../../../../components/common/ConfirmDialog';
import { LoadingSkeleton } from '../../../../components/common/LoadingSkeleton';
import { ErrorState } from '../../../../components/common/ErrorState';
import { reviewService } from '../../../../services/review.service';
import { PortfolioItem } from '../../../../types/portfolio.types';
import { SoftSkillRubricDimension, DecisionAction, RubricAssessment } from '../../../../types/review.types';
import { RUBRIC_LEVEL_LABELS } from '../../../../mocks/soft-skills-rubric.mock';
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  User,
  Calendar,
  Layers,
  FileCheck2,
  Sparkles,
  Loader2,
} from 'lucide-react';
import Link from 'next/link';

export default function TeacherReviewDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [item, setItem] = useState<PortfolioItem | null>(null);
  const [rubricDimensions, setRubricDimensions] = useState<SoftSkillRubricDimension[]>([]);
  const [rubricValues, setRubricValues] = useState<Record<string, 1 | 2 | 3 | 4 | 5>>({
    initiative: 4,
    collaboration: 4,
    communication: 3,
    responsibility: 4,
    resilience: 3,
  });

  const [feedbackNote, setFeedbackNote] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittingAction, setSubmittingAction] = useState<DecisionAction | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [actionSuccessBanner, setActionSuccessBanner] = useState('');

  // Confirmation dialogs
  const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  const fetchItemAndRubric = async () => {
    if (!id) return;
    setIsLoading(true);
    const [data, rubrics] = await Promise.all([
      reviewService.getReviewItemById(id),
      reviewService.getRubricDimensions(),
    ]);

    if (!data) {
      setErrorMsg('Portofolio karya tidak ditemukan.');
    } else {
      setItem(data);
      if (data.teacherFeedback) {
        setFeedbackNote(data.teacherFeedback);
      }
    }
    setRubricDimensions(rubrics);
    setIsLoading(false);
  };

  useEffect(() => {
    fetchItemAndRubric();
  }, [id]);

  const handleRubricChange = (dimensionId: string, value: 1 | 2 | 3 | 4 | 5) => {
    setRubricValues((prev) => ({ ...prev, [dimensionId]: value }));
  };

  const executeDecision = async (action: DecisionAction, note?: string) => {
    if (!item) return;
    setIsSubmitting(true);
    setSubmittingAction(action);
    setErrorMsg('');

    try {
      const assessments: RubricAssessment[] = rubricDimensions.map((dim) => ({
        rubricId: dim.id,
        skillName: dim.name,
        score: rubricValues[dim.id] || 3,
        label: RUBRIC_LEVEL_LABELS[rubricValues[dim.id] || 3],
      }));

      const updated = await reviewService.submitReviewDecision({
        portfolioId: item.id,
        revisionId: item.currentRevisionId,
        action,
        feedback: note || feedbackNote,
        rubricRatings: assessments,
        rubricMap: rubricValues,
      });

      setItem(updated);
      setActionSuccessBanner(
        action === 'endorse'
          ? 'Portofolio berhasil disetujui (ACC)! Skor radar kompetensi siswa telah diperbarui.'
          : action === 'request_revision'
          ? 'Catatan revisi berhasil dikirim ke siswa.'
          : 'Portofolio telah ditolak dengan alasan yang tertera.'
      );
    } catch (err: any) {
      setErrorMsg(err.message || 'Gagal menyimpan keputusan validasi.');
    } finally {
      setIsSubmitting(false);
      setSubmittingAction(null);
    }
  };

  const handleEndorse = () => {
    executeDecision('endorse', feedbackNote || 'Portofolio disetujui dan dinilai memenuhi standar kompetensi.');
  };

  const handleRequestRevision = () => {
    if (!feedbackNote.trim()) {
      setErrorMsg('Catatan revisi wajib diisi agar siswa mengetahui bagian yang harus diperbaiki.');
      return;
    }
    executeDecision('request_revision', feedbackNote);
  };

  const handleConfirmReject = () => {
    if (!rejectReason.trim()) {
      alert('Alasan penolakan wajib disertakan.');
      return;
    }
    setIsRejectDialogOpen(false);
    executeDecision('reject', rejectReason);
  };

  return (
    <AppShell pageTitle="Validasi Portofolio Siswa" expectedRole="teacher" isPageLoading={isLoading}>
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Navigation link */}
        <div className="flex items-center justify-between">
          <Link
            href="/teacher/reviews"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Kembali ke Antrean Validasi</span>
          </Link>
          {item && <span className="text-xs text-slate-400 font-mono">ID Pengajuan: {item.id}</span>}
        </div>

        {/* Success Banner */}
        {actionSuccessBanner && (
          <div className="p-4 rounded-xl bg-endorse-50 border border-endorse-300 text-endorse-800 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-endorse-600 shrink-0" />
              <p className="font-semibold">{actionSuccessBanner}</p>
            </div>
            <button
              type="button"
              onClick={() => setActionSuccessBanner('')}
              className="text-endorse-700 font-bold ml-2 text-xs"
            >
              ✕
            </button>
          </div>
        )}

        {/* Error notification */}
        {errorMsg && (
          <div className="p-4 rounded-xl bg-reject-50 border border-reject-200 text-reject-800 text-xs flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-reject-600 shrink-0 mt-0.5" />
            <p className="font-semibold">{errorMsg}</p>
          </div>
        )}

        {isLoading ? (
          <div className="bg-white p-8 rounded-2xl border border-slate-200">
            <LoadingSkeleton rows={6} />
          </div>
        ) : !item ? (
          <ErrorState
            title="Karya Tidak Ditemukan"
            message="Data karya ini mungkin tidak ada atau telah dihapus."
          />
        ) : (
          /* Split Layout: Evidence Preview (Left) vs Review Panel (Right) */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* LEFT / MAIN COLUMN: Student Work & Evidence (7 Cols) */}
            <div className="lg:col-span-7 space-y-6">
              {/* Header Box */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2 flex-wrap">
                    <StatusBadge status={item.status} size="md" />
                    <span className="text-xs text-slate-400">• {item.date}</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200" title={`ID Revisi: ${item.currentRevisionId || 'v1'}`}>
                      Snapshot Revisi: {item.currentRevisionId ? item.currentRevisionId.slice(0, 8) + '...' : 'v1'}
                    </span>
                  </div>

                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 capitalize">
                    {item.activityType}
                  </span>
                </div>

                <div className="space-y-1">
                  <h2 className="text-xl sm:text-2xl font-bold text-slate-900 leading-tight">
                    {item.title}
                  </h2>
                  <div className="flex items-center gap-2 text-xs text-slate-600 pt-1">
                    <User className="w-3.5 h-3.5 text-slate-400" />
                    <span className="font-semibold text-slate-900">{item.studentName}</span>
                    <span className="text-slate-400">• Kelas: {item.studentClass}</span>
                  </div>
                </div>

                {/* Description */}
                <div className="pt-2 border-t border-slate-100">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                    Deskripsi Karya & Peran Siswa
                  </p>
                  <p className="text-xs sm:text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                    {item.description}
                  </p>
                </div>

                {/* Tags */}
                <div className="pt-2 border-t border-slate-100">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Tag Kompetensi yang Diajukan Siswa ({item.tags.length})
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {item.tags.map((t) => (
                      <TagChip key={t} label={t} />
                    ))}
                  </div>
                </div>
              </div>

              {/* Evidence Preview Box */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-3">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Bukti Artefak / Tautan Karya (Evidence)
                </h3>
                <EvidencePreview evidence={item.evidence} />
              </div>

              {/* Validation History Timeline */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider pb-2 border-b border-slate-100">
                  Riwayat Validasi & Iterasi Siswa
                </h3>
                <ValidationTimeline events={item.timeline} />
              </div>
            </div>

            {/* RIGHT COLUMN: Review Actions & Soft Skill Rubric (5 Cols) */}
            <div className="lg:col-span-5 space-y-6">
              {/* Soft Skill Rubric Section */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
                <SoftSkillRubricForm
                  dimensions={rubricDimensions}
                  values={rubricValues}
                  onChange={handleRubricChange}
                />
              </div>

              {/* Feedback Note Input */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-3">
                <label htmlFor="feedbackNote" className="block text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Catatan Pembimbing / Alasan Validasi
                </label>
                <textarea
                  id="feedbackNote"
                  rows={3}
                  value={feedbackNote}
                  onChange={(e) => setFeedbackNote(e.target.value)}
                  placeholder="Tuliskan catatan apresiasi, saran pengembangan, atau rincian hal yang perlu direvisi siswa..."
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-growth-500 transition-colors"
                />
                <p className="text-[11px] text-slate-400">
                  Catatan ini akan langsung dapat dibaca oleh siswa di laman portofolio mereka.
                </p>

                {/* Validation Actions Panel */}
                <div className="pt-4 border-t border-slate-100 space-y-2.5">
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Keputusan Validasi:
                  </p>

                  {/* Endorse Button (Green) */}
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={handleEndorse}
                    className="w-full inline-flex items-center justify-center gap-2 py-3 px-4 rounded-xl tal-btn-emerald font-bold text-xs sm:text-sm disabled:opacity-50"
                  >
                    {submittingAction === 'endorse' ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                        <span>Memproses ACC...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Setujui Portofolio (Endorse / ACC)</span>
                      </>
                    )}
                  </button>

                  {/* Request Revision Button (Amber) */}
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={handleRequestRevision}
                    className="w-full inline-flex items-center justify-center gap-2 py-3 px-4 rounded-xl tal-btn-amber font-bold text-xs sm:text-sm disabled:opacity-50"
                  >
                    {submittingAction === 'request_revision' ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                        <span>Mengirim Catatan Revisi...</span>
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="w-4 h-4" />
                        <span>Minta Perbaikan (Request Revision)</span>
                      </>
                    )}
                  </button>

                  {/* Reject Button (Red - triggers confirmation dialog) */}
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={() => setIsRejectDialogOpen(true)}
                    className="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl tal-btn-rose font-bold text-xs disabled:opacity-50"
                  >
                    {submittingAction === 'reject' ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                        <span>Menolak Portofolio...</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-4 h-4" />
                        <span>Tolak Portofolio (Reject)</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Destructive Reject Confirmation Dialog */}
        <ConfirmDialog
          isOpen={isRejectDialogOpen}
          title="Konfirmasi Penolakan Portofolio"
          description="Apakah Anda yakin ingin menolak pengajuan karya ini? Portofolio yang ditolak tidak akan berkontribusi pada radar kompetensi atau Digital CV siswa."
          confirmLabel="Ya, Tolak Karya"
          cancelLabel="Kembali"
          variant="danger"
          isSubmitting={isSubmitting}
          onConfirm={handleConfirmReject}
          onCancel={() => setIsRejectDialogOpen(false)}
        >
          <div className="space-y-1.5 mt-2">
            <label htmlFor="rejectReason" className="block text-xs font-bold text-slate-700 uppercase">
              Alasan Penolakan <span className="text-reject-500">*</span>:
            </label>
            <textarea
              id="rejectReason"
              rows={2}
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Contoh: Bukti tidak relevan dengan kompetensi pembelajaran..."
              className="w-full p-2.5 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-reject-500"
            />
          </div>
        </ConfirmDialog>
      </div>
    </AppShell>
  );
}
