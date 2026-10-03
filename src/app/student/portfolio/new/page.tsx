'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '../../../../components/layout/AppShell';
import { portfolioService } from '../../../../services/portfolio.service';
import { CanonicalTag, EvidenceSource } from '../../../../types/portfolio.types';
import {
  ArrowLeft,
  Upload,
  Link as LinkIcon,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  Send,
  FileText,
} from 'lucide-react';
import Link from 'next/link';
import { cn } from '../../../../lib/utils';

export default function NewPortfolioPage() {
  const router = useRouter();

  // Form fields matching 08-Student-Upload-HF.svg
  const [title, setTitle] = useState('');
  const [role, setRole] = useState('');
  const [problemSolved, setProblemSolved] = useState('');
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>(['tag-1', 'tag-2', 'tag-3']);
  const [availableTags, setAvailableTags] = useState<CanonicalTag[]>([]);

  // Evidence mode: file vs link
  const [evidenceMode, setEvidenceMode] = useState<'file' | 'link'>('file');
  const [fileName, setFileName] = useState<string | null>('Waste2Wisdom-Documentation.pdf');
  const [linkUrl, setLinkUrl] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    portfolioService.getCanonicalTags().then((tags) => {
      setAvailableTags(tags);
      if (tags.length >= 3 && selectedTagIds.length === 0) {
        setSelectedTagIds(tags.slice(0, 3).map((t) => t.id));
      }
    });
  }, []);

  const toggleTag = (tagId: string) => {
    if (selectedTagIds.includes(tagId)) {
      setSelectedTagIds(selectedTagIds.filter((id) => id !== tagId));
    } else {
      if (selectedTagIds.length >= 5) {
        setErrorMsg('Maksimal 5 capability tags diperbolehkan.');
        return;
      }
      setSelectedTagIds([...selectedTagIds, tagId]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (!title.trim()) {
      setErrorMsg('Nama proyek / kegiatan wajib diisi.');
      return;
    }
    if (!role.trim() && !problemSolved.trim()) {
      setErrorMsg('Ceritakan peran atau masalah yang kamu selesaikan.');
      return;
    }
    if (selectedTagIds.length < 3 || selectedTagIds.length > 5) {
      setErrorMsg('Pilih 3–5 capability tags.');
      return;
    }

    setIsSubmitting(true);
    try {
      const fullDesc = `Peran: ${role || 'Lead / Kontributor'}. Masalah & Solusi: ${problemSolved || 'Menyelesaikan permasalahan dan menghasilkan dampak nyata.'}`;
      const evidence: EvidenceSource =
        evidenceMode === 'file'
          ? {
              type: 'file',
              url: '/mock-uploads/' + (fileName || 'dokumentasi.pdf'),
              fileName: fileName || 'Dokumen_Bukti.pdf',
              fileSize: '1.8 MB',
            }
          : {
              type: 'link',
              url: linkUrl || 'https://github.com/project',
            };

      await portfolioService.createPortfolioItem({
        title,
        activityType: 'project',
        date: new Date().toISOString().split('T')[0],
        description: fullDesc,
        tags: selectedTagIds,
        evidence,
        status: 'submitted',
        studentId: 'student-demo',
        studentName: 'Raihan Ansari',
        studentClass: 'XII IPA 2',
      });

      router.push('/student/portfolio');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal mengirim karya ke guru.';
      setErrorMsg(msg);
      setIsSubmitting(false);
    }
  };

  const selectedTags = availableTags.filter((t) => selectedTagIds.includes(t.id));

  return (
    <AppShell pageTitle="Tambah Proof of Work" expectedRole="student">
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header matching 08-Student-Upload-HF.svg */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Link
                href="/student/portfolio"
                className="text-xs font-bold text-[#6D28D9] hover:text-[#8B5CF6] inline-flex items-center gap-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Kembali ke Portofolio</span>
              </Link>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              Tambah Proof of Work
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Isi singkat, pilih capability tags, lalu kirim ke guru.
            </p>
          </div>

          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FAF5FF] border border-[#E9E1F4] text-[#A78BFA] font-bold text-xs shadow-xs self-start sm:self-auto">
            <span>Semester 5</span>
          </div>
        </div>

        {errorMsg && (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* 2-Column Upload Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Form (7 cols) */}
          <form onSubmit={handleSubmit} className="lg:col-span-7 space-y-6">
            {/* Step 1: Karya Kamu */}
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-4">
              <h2 className="text-base font-extrabold text-[#261331]">1. Karya kamu</h2>

              <div className="flex items-center gap-2 pb-2">
                <button
                  type="button"
                  onClick={() => setEvidenceMode('file')}
                  className={cn(
                    'px-4 py-1.5 rounded-full text-xs font-bold transition-all',
                    evidenceMode === 'file'
                      ? 'tal-btn-primary shadow-xs'
                      : 'bg-[#F7F2FF] text-[#6D28D9]'
                  )}
                >
                  Upload File
                </button>
                <button
                  type="button"
                  onClick={() => setEvidenceMode('link')}
                  className={cn(
                    'px-4 py-1.5 rounded-full text-xs font-bold transition-all',
                    evidenceMode === 'link'
                      ? 'tal-btn-primary shadow-xs'
                      : 'bg-[#F7F2FF] text-[#6D28D9]'
                  )}
                >
                  Tempel Tautan
                </button>
              </div>

              {evidenceMode === 'file' ? (
                <div
                  onClick={() => setFileName('Waste2Wisdom-Submission.pdf')}
                  className="border-2 border-dashed border-purple-200 hover:border-purple-400 bg-[#FCFBFF] rounded-2xl p-6 text-center cursor-pointer transition-colors space-y-2"
                >
                  <div className="w-10 h-10 rounded-full bg-purple-100 text-[#6D28D9] flex items-center justify-center mx-auto">
                    <Upload className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[#261331]">
                      {fileName || 'Tarik file ke sini atau pilih dari perangkat'}
                    </p>
                    <p className="text-[11px] text-[#6F607D] mt-0.5">
                      PDF, JPG, PNG, MP4 (Maks. mengikuti kuota sekolah)
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#6F607D]">
                    Atau tempel tautan karya
                  </label>
                  <input
                    type="url"
                    value={linkUrl}
                    onChange={(e) => setLinkUrl(e.target.value)}
                    placeholder="https://github.com/username/project"
                    className="w-full px-4 py-2.5 bg-white border border-[#E9E1F4] rounded-xl text-xs text-[#261331] placeholder-[#9584A7] focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                  />
                </div>
              )}
            </div>

            {/* Step 2: Konteks Karya */}
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-4">
              <h2 className="text-base font-extrabold text-[#261331]">2. Ceritakan konteks karya</h2>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#6F607D]">
                  Nama proyek / kegiatan
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Contoh: Platform Edukasi Limbah Waste2Wisdom"
                  className="w-full px-4 py-2.5 bg-white border border-[#E9E1F4] rounded-xl text-xs text-[#261331] placeholder-[#9584A7] focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#6F607D]">
                  Apa peranmu?
                </label>
                <input
                  type="text"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  placeholder="Contoh: Frontend Lead Developer & UX Researcher"
                  className="w-full px-4 py-2.5 bg-white border border-[#E9E1F4] rounded-xl text-xs text-[#261331] placeholder-[#9584A7] focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#6F607D]">
                  Apa masalah yang kamu selesaikan?
                </label>
                <textarea
                  rows={3}
                  value={problemSolved}
                  onChange={(e) => setProblemSolved(e.target.value)}
                  placeholder="Jelaskan tantangan, dampak nyata, atau hasil dari proyek kamu..."
                  className="w-full px-4 py-2.5 bg-white border border-[#E9E1F4] rounded-xl text-xs text-[#261331] placeholder-[#9584A7] focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
                />
              </div>
            </div>

            {/* Step 3: Capability Tags */}
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-extrabold text-[#261331]">
                  3. Pilih 3–5 capability tags
                </h2>
                <span className="text-xs font-bold text-[#6D28D9]">
                  {selectedTagIds.length}/5 terpilih
                </span>
              </div>

              <div className="flex flex-wrap gap-2">
                {availableTags.map((tag) => {
                  const isSelected = selectedTagIds.includes(tag.id);
                  return (
                    <button
                      key={tag.id}
                      type="button"
                      onClick={() => toggleTag(tag.id)}
                      className={cn(
                        'px-3.5 py-1.5 rounded-full text-xs font-bold transition-all flex items-center gap-1.5',
                        isSelected
                          ? 'tal-btn-primary shadow-xs'
                          : 'bg-[#F7F2FF] text-[#6D28D9] border border-purple-100 hover:border-purple-300'
                      )}
                    >
                      <span>#{tag.label || tag.id}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Submit Action */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3.5 rounded-xl tal-btn-primary font-bold text-sm shadow-md flex items-center justify-center gap-2 hover:scale-[1.01] transition-transform disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              <span>{isSubmitting ? 'Mengirim...' : 'Kirim ke guru'}</span>
            </button>
          </form>

          {/* Right Column: Live Preview & Validation Flow (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Live Preview Card matching 08-Student-Upload-HF.svg */}
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-extrabold text-[#6F607D] uppercase tracking-wider">
                  Live preview
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600">
                  DRAFT
                </span>
              </div>

              <div className="p-4 rounded-xl bg-[#FCFBFF] border border-[#E9E1F4] space-y-2">
                <h4 className="text-base font-extrabold text-[#261331]">
                  {title || 'Waste2Wisdom'}
                </h4>
                <p className="text-xs text-[#6F607D]">
                  {role || 'Platform Edukasi Limbah'}
                </p>

                <div className="flex flex-wrap gap-1.5 pt-2">
                  {(selectedTags.length > 0 ? selectedTags : [{ id: '1', label: 'WebDev' }, { id: '2', label: 'Teamwork' }]).map((t) => (
                    <span
                      key={t.id}
                      className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#F3E8FF] text-[#6D28D9]"
                    >
                      #{t.label || t.id}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-[#FAF5FF] border border-purple-100 text-center">
                <p className="text-[11px] font-semibold text-[#6D28D9]">
                  Belum memengaruhi Skill Map.
                </p>
              </div>
            </div>

            {/* Alur Validasi Diagram matching 08-Student-Upload-HF.svg */}
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-4">
              <h3 className="text-xs font-extrabold text-[#6F607D] uppercase tracking-wider">
                Alur validasi
              </h3>

              <div className="space-y-3">
                {[
                  { step: '1', text: 'Kamu kirim karya' },
                  { step: '2', text: 'Guru memeriksa' },
                  { step: '3', text: 'Endorse / Revisi' },
                  { step: '4', text: 'Masuk Skill Map' },
                ].map((item) => (
                  <div key={item.step} className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-full tal-btn-primary font-bold text-xs flex items-center justify-center shrink-0">
                      {item.step}
                    </div>
                    <span className="text-xs font-bold text-[#261331]">{item.text}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
