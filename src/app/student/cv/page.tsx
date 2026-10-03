'use client';

import React, { useEffect, useState } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';
import { cvService } from '../../../services/cv.service';
import { CVBuilderContext, CVGenerateResponse } from '../../../types/cv.types';
import {
  FileCheck2,
  Download,
  QrCode,
  CheckCircle2,
  ShieldCheck,
  Check,
  Sparkles,
  ExternalLink,
  Loader2,
} from 'lucide-react';
import { authService } from '../../../services/auth.service';
import Link from 'next/link';
import { cn } from '../../../lib/utils';

export default function StudentCVPage() {
  const [context, setContext] = useState<CVBuilderContext | null>(null);
  const [currentUser, setCurrentUser] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<string[]>(['1', '2', '3', '4']);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedCv, setGeneratedCv] = useState<CVGenerateResponse | null>(null);

  const mockAvailableEvidences = [
    { id: '1', title: 'Waste2Wisdom', category: 'Web Platform' },
    { id: '2', title: 'Robot Line Follower', category: 'Hardware & IoT' },
    { id: '3', title: 'Class Meeting Leadership', category: 'Event Management' },
    { id: '4', title: 'Presentasi Sejarah Nusantara', category: 'Public Speaking' },
    { id: '5', title: 'Festival Seni Sekolah', category: 'Creative' },
    { id: '6', title: 'Lomba Cerdas Cermat', category: 'Analysis' },
  ];

  useEffect(() => {
    authService.getCurrentSession().then((s) => {
      if (s.user?.name) setCurrentUser(s.user.name);
    });

    cvService
      .getCVBuilderContext()
      .then((data) => {
        setContext(data);
        if (data.approvedPortfolios && data.approvedPortfolios.length > 0) {
          setSelectedIds(data.approvedPortfolios.slice(0, 4).map((p) => p.portfolioId));
        }
      })
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  const toggleSelect = (id: string) => {
    if (selectedIds.includes(id)) {
      if (selectedIds.length <= 1) return;
      setSelectedIds(selectedIds.filter((item) => item !== id));
    } else {
      if (selectedIds.length >= 8) return;
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const res = await cvService.generateCV({
        portfolioIds: selectedIds,
        includeTeacherCompetencies: true,
        includeExploration: true,
      });
      setGeneratedCv(res);
    } catch {
      // Demo fallback
      setGeneratedCv({
        snapshotId: 'snap-v1',
        displayCode: 'TLN-CV-2026',
        contentDigest: 'sha256-mock-digest',
        fingerprint: 'TLN-94B8-E210',
        status: 'active',
        selectedProjectCount: selectedIds.length,
        verificationToken: 'tlnt_token_v94b8e21',
        verificationUrl: '/verify/tlnt_token_v94b8e21',
        issuedAt: new Date().toISOString(),
        expiresAt: null,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <AppShell pageTitle="Digital CV" expectedRole="student">
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header matching 11-Student-DigitalCV-HF.svg */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              Digital CV
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Pilih evidence tervalidasi, generate PDF, lalu verifikasi melalui QR unik.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FAF5FF] border border-[#E9E1F4] text-[#A78BFA] font-bold text-xs shadow-xs self-start sm:self-auto">
            <span>Semester 5</span>
          </div>
        </div>

        {/* 2-Column CV Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Live CV Document Preview (7 cols) */}
          <div className="lg:col-span-7 bg-white rounded-[22px] border border-[#E9E1F4] p-8 shadow-[0_8px_30px_rgba(76,29,149,0.08)] space-y-6 relative overflow-hidden">
            <div className="flex items-center justify-between pb-4 border-b border-[#E9E1F4]">
              <span className="text-xs font-extrabold text-[#9584A7] tracking-wider uppercase">
                PREVIEW CV
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#F3E8FF] text-[#6D28D9]">
                DRAFT PREVIEW
              </span>
            </div>

            {/* Document Header */}
            <div>
              <h2 className="text-2xl font-black text-[#261331] tracking-tight uppercase">
                {currentUser || context?.profile?.displayName || 'Dimas Pratama'}
              </h2>
              <p className="text-xs font-bold text-[#6D28D9] mt-0.5">
                Student Portfolio • Software & Product
              </p>
            </div>

            {/* Profile Section */}
            <div className="space-y-1">
              <h3 className="text-[10px] font-extrabold text-[#9584A7] uppercase tracking-wider">
                PROFILE
              </h3>
              <p className="text-xs text-[#261331] leading-relaxed">
                Evidence-driven student portfolio with validated project work.
              </p>
            </div>

            {/* Selected Projects */}
            <div className="space-y-3">
              <h3 className="text-[10px] font-extrabold text-[#9584A7] uppercase tracking-wider">
                SELECTED PROJECTS
              </h3>
              <div className="space-y-2.5 text-xs">
                {mockAvailableEvidences
                  .filter((e) => selectedIds.includes(e.id))
                  .slice(0, 3)
                  .map((e) => (
                    <div key={e.id} className="p-3 rounded-xl bg-[#FCFBFF] border border-[#E9E1F4]">
                      <p className="font-extrabold text-[#261331]">{e.title} — {e.category}</p>
                      <p className="text-[10px] text-[#059669] font-semibold mt-0.5">
                        ✓ Validated by school teacher
                      </p>
                    </div>
                  ))}
              </div>
            </div>

            {/* Verified Skills */}
            <div className="space-y-2">
              <h3 className="text-[10px] font-extrabold text-[#9584A7] uppercase tracking-wider">
                VERIFIED SKILLS
              </h3>
              <div className="flex flex-wrap gap-2">
                {['WebDev', 'Leadership', 'Communication', 'ProblemSolving'].map((s) => (
                  <span
                    key={s}
                    className="px-3 py-1 rounded-full text-xs font-bold bg-[#F7F2FF] text-[#6D28D9] border border-purple-100"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>

            {/* QR Verified Badge Box */}
            <div className="p-4 rounded-2xl bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white p-2 shadow-xs border border-purple-100 flex items-center justify-center">
                  <QrCode className="w-6 h-6 text-[#6D28D9]" />
                </div>
                <div>
                  <p className="text-xs font-extrabold text-[#261331]">QR AUTHENTICITY</p>
                  <p className="text-[10px] text-[#6F607D]">Otentisitas resmi tervalidasi</p>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-black bg-emerald-100 text-emerald-800">
                VERIFIED
              </span>
            </div>
          </div>

          {/* Right Column: Controls & Selection (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            {/* Readiness Card */}
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-extrabold text-[#6F607D] uppercase">
                  CV readiness
                </h3>
                <span className="text-xl font-extrabold text-[#6D28D9]">76%</span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-[#F3E8FF] overflow-hidden">
                <div className="h-full rounded-full tal-btn-primary" style={{ width: '76%' }} />
              </div>
              <p className="text-xs text-[#6F607D]">
                {selectedIds.length} dari {mockAvailableEvidences.length} evidence dipilih
              </p>
            </div>

            {/* Evidence Checklist */}
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-4">
              <h3 className="text-xs font-extrabold text-[#6F607D] uppercase tracking-wider">
                Evidence terpilih
              </h3>

              <div className="space-y-2.5">
                {mockAvailableEvidences.map((e) => {
                  const isChecked = selectedIds.includes(e.id);
                  return (
                    <div
                      key={e.id}
                      onClick={() => toggleSelect(e.id)}
                      className={cn(
                        'p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all',
                        isChecked
                          ? 'bg-[#F7F2FF] border-purple-200 text-[#261331]'
                          : 'bg-white border-[#E9E1F4] text-[#6F607D]'
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={cn(
                            'w-5 h-5 rounded-md flex items-center justify-center text-xs font-bold transition-colors',
                            isChecked ? 'tal-btn-primary text-white' : 'border border-slate-300'
                          )}
                        >
                          {isChecked && <Check className="w-3.5 h-3.5" />}
                        </div>
                        <span className="text-xs font-bold">{e.title}</span>
                      </div>
                      <span className="text-[10px] text-[#9584A7]">{e.category}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Verification Ready Card */}
            <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-extrabold text-[#261331]">Verifikasi</h4>
                  <p className="text-[11px] text-[#6F607D] mt-0.5">
                    Aktif setelah CV diterbitkan.
                  </p>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#ECFDF5] text-[#059669] border border-emerald-200">
                  QR READY
                </span>
              </div>

              <button
                type="button"
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full py-3.5 rounded-xl tal-btn-primary font-bold text-sm shadow-md flex items-center justify-center gap-2 hover:scale-[1.01] transition-transform disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-white" />
                    <span>Menerbitkan CV...</span>
                  </>
                ) : (
                  <>
                    <FileCheck2 className="w-4 h-4" />
                    <span>Generate CV PDF</span>
                  </>
                )}
              </button>

              {generatedCv && (
                <div className="p-4 rounded-xl bg-purple-50 border border-purple-200 space-y-2 animate-in fade-in">
                  <p className="text-xs font-bold text-[#6D28D9]">✓ CV Resmi Berhasil Diterbitkan</p>
                  <div className="flex items-center gap-2 pt-1">
                    <Link
                      href={generatedCv.verificationUrl || `/verify/${generatedCv.verificationToken || 'tlnt_token_v94b8e21'}`}
                      target="_blank"
                      className="text-xs font-bold text-[#6D28D9] hover:underline inline-flex items-center gap-1"
                    >
                      <span>Buka Halaman Verifikasi Publik</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
