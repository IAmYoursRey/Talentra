'use client';

import React, { useEffect, useState } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { reviewService } from '../../../services/review.service';
import { PortfolioItem } from '../../../types/portfolio.types';
import {
  Inbox,
  Clock,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Send,
  Check,
  ChevronRight,
  ShieldCheck,
  Loader2,
} from 'lucide-react';
import { cn } from '../../../lib/utils';

export default function TeacherReviewQueuePage() {
  const [queue, setQueue] = useState<PortfolioItem[]>([]);
  const [selectedId, setSelectedId] = useState<string>('p-1');
  const [rubricScores, setRubricScores] = useState<Record<string, number>>({
    Initiative: 4,
    Collaboration: 5,
    Communication: 4,
    Responsibility: 5,
  });
  const [teacherNotes, setTeacherNotes] = useState('Tambahkan dokumentasi proses testing.');
  const [actionNotice, setActionNotice] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittingAction, setSubmittingAction] = useState<'endorse' | 'revision' | 'reject' | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    reviewService
      .getReviewQueue()
      .then((items) => {
        if (items && items.length > 0) {
          setQueue(items);
          setSelectedId(items[0].id);
        }
      })
      .catch(() => null)
      .finally(() => setIsLoading(false));
  }, []);

  const fallbackQueue = [
    {
      id: 'p-1',
      studentName: 'Dimas Pratama',
      studentClass: 'XII IPA 2',
      title: 'Website Waste2Wisdom',
      initials: 'DP',
      desc: 'Connecting waste, ideas, and local impact.',
      tags: ['WebDev', 'ProblemSolving', 'Teamwork'],
    },
    {
      id: 'p-2',
      studentName: 'Nabila K.',
      studentClass: 'XI IPA 1',
      title: 'Video Kampanye Sekolah',
      initials: 'NK',
      desc: 'Kampanye kesadaran kebersihan lingkungan sekolah berbasis video visual.',
      tags: ['Creative', 'Communication', 'Teamwork'],
    },
    {
      id: 'p-3',
      studentName: 'Arya F.',
      studentClass: 'XII IPA 1',
      title: 'Robot Line Follower',
      initials: 'AF',
      desc: 'Robot line follower analog untuk kompetisi robotika regional.',
      tags: ['Engineering', 'ProblemSolving', 'Analysis'],
    },
    {
      id: 'p-4',
      studentName: 'Salsa A.',
      studentClass: 'XI IPA 2',
      title: 'Festival Seni',
      initials: 'SA',
      desc: 'Manajemen kepanitiaan festival budaya dan kesenian tahunan.',
      tags: ['Leadership', 'Teamwork', 'Communication'],
    },
    {
      id: 'p-5',
      studentName: 'Dimas N.',
      studentClass: 'X IPA 1',
      title: 'Poster Data',
      initials: 'DN',
      desc: 'Infografis visualisasi data demografi siswa sekolah.',
      tags: ['Design', 'Analysis'],
    },
  ];

  const currentItem = fallbackQueue.find((q) => q.id === selectedId) || fallbackQueue[0];

  const handleAction = (decision: 'endorse' | 'revision' | 'reject') => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setSubmittingAction(decision);
    setTimeout(() => {
      setIsSubmitting(false);
      setSubmittingAction(null);
      if (decision === 'endorse') {
        setActionNotice(`Karya "${currentItem.title}" berhasil di-Endorse dan diproyeksikan ke Skill Map siswa.`);
      } else if (decision === 'revision') {
        setActionNotice(`Permintaan revisi untuk "${currentItem.title}" telah dikirim ke siswa.`);
      } else {
        setActionNotice(`Karya "${currentItem.title}" telah ditolak dengan catatan.`);
      }
      setTimeout(() => setActionNotice(''), 4000);
    }, 600);
  };

  return (
    <AppShell pageTitle="Approval Queue" expectedRole="teacher" isPageLoading={isLoading}>
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header matching 13-Teacher-Approval-HF.svg */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              Approval Queue
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Validasi karya siswa dan berikan umpan balik berbasis rubrik.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FAF5FF] border border-[#E9E1F4] text-[#A78BFA] font-bold text-xs shadow-xs self-start sm:self-auto">
            <Clock className="w-3.5 h-3.5" />
            <span>18 menunggu</span>
          </div>
        </div>

        {actionNotice && (
          <div className="p-4 rounded-xl bg-purple-50 border border-purple-200 text-[#6D28D9] text-xs font-bold flex items-center gap-2 animate-in fade-in">
            <CheckCircle2 className="w-4 h-4 text-[#6D28D9] shrink-0" />
            <span>{actionNotice}</span>
          </div>
        )}

        {/* 2-Column Approval Interface matching 13-Teacher-Approval-HF.svg */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Antrean hari ini (5 cols) */}
          <div className="lg:col-span-5 bg-white rounded-[18px] border border-[#E9E1F4] p-5 sm:p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-4">
            <div>
              <h2 className="text-base font-extrabold text-[#261331]">Antrean hari ini</h2>
              <p className="text-xs text-[#6F607D] mt-0.5">
                Urut berdasarkan waktu masuk
              </p>
            </div>

            <div className="space-y-2.5">
              {fallbackQueue.map((item) => {
                const isSelected = item.id === selectedId;
                return (
                  <div
                    key={item.id}
                    onClick={() => setSelectedId(item.id)}
                    className={cn(
                      'p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3',
                      isSelected
                        ? 'bg-[#F7F2FF] border-[#8B5CF6] shadow-xs'
                        : 'bg-[#FCFBFF] border-[#E9E1F4] hover:border-purple-200'
                    )}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div
                        className={cn(
                          'w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs shrink-0',
                          isSelected ? 'tal-btn-primary text-white' : 'bg-purple-100 text-[#6D28D9]'
                        )}
                      >
                        {item.initials}
                      </div>
                      <div className="min-w-0">
                        <h3 className="text-xs font-extrabold text-[#261331] truncate">
                          {item.studentName}
                        </h3>
                        <p className="text-[11px] text-[#6F607D] truncate">
                          {item.title}
                        </p>
                      </div>
                    </div>

                    {isSelected && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#8B5CF6] text-white shrink-0">
                        Dipilih
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Review Detail & Scoring Form (7 cols) */}
          <div className="lg:col-span-7 bg-white rounded-[18px] border border-[#E9E1F4] p-6 sm:p-8 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-6">
            {/* Title & Subtitle */}
            <div className="pb-4 border-b border-[#E9E1F4] space-y-2">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h2 className="text-xl font-black text-[#261331]">
                  {currentItem.title}
                </h2>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#F3E8FF] text-[#6D28D9] border border-purple-100">
                  {currentItem.tags.length} tags
                </span>
              </div>
              <p className="text-xs font-semibold text-[#6F607D]">
                {currentItem.studentName} • {currentItem.studentClass}
              </p>
              <p className="text-xs text-[#261331] pt-1">
                {currentItem.desc}
              </p>
            </div>

            {/* Capability Tags */}
            <div className="space-y-2">
              <span className="text-[10px] font-extrabold text-[#9584A7] uppercase tracking-wider block">
                Capability tags
              </span>
              <div className="flex flex-wrap gap-2">
                {currentItem.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1 rounded-full text-xs font-bold bg-[#F7F2FF] text-[#6D28D9] border border-purple-100"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Rubrik Soft Skill */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-extrabold text-[#261331]">
                  Rubrik soft skill
                </span>
                <span className="text-[11px] text-[#9584A7]">Skor 1 hingga 5</span>
              </div>

              <div className="space-y-2.5">
                {['Initiative', 'Collaboration', 'Communication', 'Responsibility'].map((dim) => {
                  const score = rubricScores[dim] || 4;
                  return (
                    <div
                      key={dim}
                      className="p-3 rounded-xl bg-[#FCFBFF] border border-[#E9E1F4] flex items-center justify-between gap-4"
                    >
                      <span className="text-xs font-bold text-[#261331]">{dim}</span>
                      <div className="flex items-center gap-1.5">
                        {[1, 2, 3, 4, 5].map((val) => (
                          <button
                            key={val}
                            type="button"
                            onClick={() => setRubricScores({ ...rubricScores, [dim]: val })}
                            className={cn(
                              'w-7 h-7 rounded-lg text-xs font-extrabold tal-pill-btn',
                              score === val
                                ? 'tal-btn-primary'
                                : 'bg-white border border-[#E9E1F4] text-[#6F607D] hover:border-purple-300 hover:bg-[#FAF7FD]'
                            )}
                          >
                            {val}
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Catatan Guru */}
            <div className="space-y-1.5">
              <label className="text-xs font-extrabold text-[#261331] block">
                Catatan guru
              </label>
              <textarea
                rows={3}
                value={teacherNotes}
                onChange={(e) => setTeacherNotes(e.target.value)}
                placeholder="Berikan masukan atau catatan perbaikan untuk siswa..."
                className="w-full px-4 py-2.5 bg-white border border-[#E9E1F4] rounded-xl text-xs text-[#261331] placeholder-[#9584A7] focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
              />
            </div>

            {/* Action Buttons matching 13-Teacher-Approval-HF.svg */}
            <div className="pt-2 flex items-center gap-3">
              <button
                type="button"
                onClick={() => handleAction('reject')}
                disabled={isSubmitting}
                className="px-5 py-2.5 rounded-xl tal-btn-rose font-bold text-xs inline-flex items-center gap-1.5 disabled:opacity-50"
              >
                {submittingAction === 'reject' && <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />}
                <span>{submittingAction === 'reject' ? 'Menolak...' : 'Tolak'}</span>
              </button>
              <button
                type="button"
                onClick={() => handleAction('revision')}
                disabled={isSubmitting}
                className="px-5 py-2.5 rounded-xl tal-btn-amber font-bold text-xs inline-flex items-center gap-1.5 disabled:opacity-50"
              >
                {submittingAction === 'revision' && <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />}
                <span>{submittingAction === 'revision' ? 'Mengirim...' : 'Minta revisi'}</span>
              </button>
              <button
                type="button"
                onClick={() => handleAction('endorse')}
                disabled={isSubmitting}
                className="flex-1 py-2.5 rounded-xl tal-btn-emerald font-bold text-xs flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {submittingAction === 'endorse' ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-white" />
                    <span>Memproses Endorse...</span>
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Endorse karya</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
