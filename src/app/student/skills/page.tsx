'use client';

import React, { useEffect, useState } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { SkillRadarChart } from '../../../components/charts/SkillRadarChart';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';
import { skillService } from '../../../services/skill.service';
import { SkillSnapshot, SkillDetail } from '../../../types/skill.types';
import {
  TrendingUp,
  Award,
  Layers,
  ChevronRight,
  Info,
  Calendar,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react';
import Link from 'next/link';

export default function StudentSkillsPage() {
  const [snapshot, setSnapshot] = useState<SkillSnapshot | null>(null);
  const [selectedSkill, setSelectedSkill] = useState<string>('Web Development');
  const [skillDetail, setSkillDetail] = useState<SkillDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadSkillData = async () => {
      setIsLoading(true);
      const data = await skillService.getStudentSkillSnapshot();
      setSnapshot(data);
      if (data.radarPoints.length > 0) {
        const initialSkill = data.radarPoints[0].skill;
        setSelectedSkill(initialSkill);
        const detail = await skillService.getSkillDetail(initialSkill);
        setSkillDetail(detail);
      }
      setIsLoading(false);
    };

    loadSkillData();
  }, []);

  const handleSelectSkill = async (skillName: string) => {
    setSelectedSkill(skillName);
    const detail = await skillService.getSkillDetail(skillName);
    setSkillDetail(detail);
  };

  return (
    <AppShell pageTitle="Peta Kompetensi & Skill" expectedRole="student">
      <div className="space-y-6">
        {/* Header Banner */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-xs space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-growth-50 text-growth-700 border border-growth-200">
              Scoring Engine: {snapshot?.scoringVersion || 'approved-evidence-count-v1'}
            </span>
            <span className="text-xs text-slate-400">• Pembaruan: {snapshot?.lastCalculatedAt}</span>
          </div>

          <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
            Peta Talenta & Perkembangan Kompetensi
          </h2>

          <p className="text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed">
            Indeks ini menunjukkan kekuatan bukti dari karya yang telah disetujui guru, bukan nilai mutlak kemampuan.
          </p>

          <div className="pt-2 flex items-center gap-2 text-xs text-slate-500">
            <Info className="w-4 h-4 text-growth-600 shrink-0" />
            <span className="italic">
              &ldquo;Hanya karya tervalidasi pembimbing yang berkontribusi terhadap indeks ini (min 100, unit bukti x 20).&rdquo;
            </span>
          </div>
        </div>

        {/* Top 3 Skills Highlight Row */}
        {snapshot?.topSkills && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {snapshot.topSkills.map((sk, idx) => (
              <div
                key={sk.name}
                onClick={() => handleSelectSkill(sk.name)}
                className={`p-4 rounded-xl border transition-all cursor-pointer bg-white shadow-2xs hover:border-growth-400 ${
                  selectedSkill === sk.name ? 'ring-2 ring-growth-500 border-growth-500' : 'border-slate-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-400">Peringkat #{idx + 1}</span>
                  <span className="text-xs font-bold text-growth-700 bg-growth-50 px-2 py-0.5 rounded border border-growth-200">
                    Skor {sk.score}
                  </span>
                </div>
                <p className="text-sm font-bold text-slate-900 mt-2">{sk.name}</p>
                <p className="text-xs text-slate-500 mt-0.5">{sk.level}</p>
              </div>
            ))}
          </div>
        )}

        {/* Two-Column: Large Radar Chart & Evidence Contributors Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Large Radar Chart (7 cols) */}
          <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-growth-50 text-growth-700 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Radar Dimensi Kompetensi</h3>
                  <p className="text-xs text-slate-500">6 klaster kapabilitas siswa</p>
                </div>
              </div>
            </div>

            {isLoading ? (
              <LoadingSkeleton rows={5} />
            ) : (
              <SkillRadarChart
                data={snapshot?.radarPoints || []}
                height={340}
                showTextAlternative={true}
              />
            )}

            {/* Clickable selector chips to inspect each dimension */}
            <div className="pt-3 border-t border-slate-100">
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                Pilih Dimensi untuk Melihat Bukti yang Berkontribusi:
              </p>
              <div className="flex flex-wrap gap-1.5">
                {snapshot?.radarPoints.map((pt) => (
                  <button
                    key={pt.skill}
                    type="button"
                    onClick={() => handleSelectSkill(pt.skill)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      selectedSkill === pt.skill
                        ? 'bg-growth-600 text-white shadow-2xs'
                        : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                    }`}
                  >
                    {pt.skill} ({pt.score})
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Evidence Contributors (5 cols) */}
          <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs flex flex-col justify-between space-y-4">
            <div className="space-y-4">
              <div className="pb-3 border-b border-slate-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Evidence Contributors
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs font-bold bg-growth-50 text-growth-700 border border-growth-200">
                    Skor: {skillDetail?.score || 0} / 100
                  </span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 mt-1">{selectedSkill}</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Daftar karya terverifikasi yang mendasari perhitungan skor keahlian ini.
                </p>
              </div>

              {/* Contributors list */}
              {skillDetail?.contributors && skillDetail.contributors.length > 0 ? (
                <div className="space-y-3">
                  {skillDetail.contributors.map((c) => (
                    <div
                      key={c.portfolioId}
                      className="p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/70 hover:bg-slate-50 transition-colors space-y-2"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <Link
                          href={`/student/portfolio/${c.portfolioId}`}
                          className="text-xs font-bold text-slate-900 hover:text-brand-600 line-clamp-2"
                        >
                          {c.portfolioTitle}
                        </Link>
                        <span className="text-[11px] font-bold text-growth-700 shrink-0">
                          +{c.contributionScore} pts
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-200/50">
                        <span className="capitalize">{c.activityType}</span>
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3 text-slate-400" />
                          <span>{c.date}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Belum ada karya tervalidasi yang memuat tag untuk kompetensi ini.
                  </p>
                  <Link
                    href="/student/portfolio/new"
                    className="inline-block mt-3 text-xs font-bold text-brand-600 hover:underline"
                  >
                    + Ajukan Karya Terkait
                  </Link>
                </div>
              )}
            </div>

            {/* Rubric Notes */}
            <div className="p-3 bg-growth-50/50 border border-growth-200/70 rounded-xl text-xs text-growth-900 space-y-1">
              <p className="font-bold flex items-center gap-1.5 text-growth-800">
                <CheckCircle2 className="w-3.5 h-3.5 text-growth-600" />
                <span>Prinsip Keabsahan Sinyal Talenta</span>
              </p>
              <p className="text-[11px] leading-relaxed text-growth-800">
                Setiap poin kalkulasi kompetensi memiliki bukti digital yang dapat diverifikasi oleh pihak kampus atau industri melalui QR Code resmi.
              </p>
            </div>
          </div>
        </div>

        {/* Teacher Soft-Skill Rubric Observations Section (Distinct from Evidence Radar) */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Observasi Karakter & Soft-Skill Guru</h3>
              <p className="text-xs text-slate-500">
                Rata-rata penilaian rubrik 1–5 oleh guru pembimbing pada karya yang telah disetujui. Ditampilkan terpisah dari indeks kekuatan bukti portofolio.
              </p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">
              5 Dimensi Observasi
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {(snapshot?.teacherRubrics || [
              { dimensionCode: 'initiative', displayName: 'Inisiatif', averageScore: 0, assessmentCount: 0 },
              { dimensionCode: 'collaboration', displayName: 'Kolaborasi', averageScore: 0, assessmentCount: 0 },
              { dimensionCode: 'communication', displayName: 'Komunikasi', averageScore: 0, assessmentCount: 0 },
              { dimensionCode: 'responsibility', displayName: 'Tanggung Jawab', averageScore: 0, assessmentCount: 0 },
              { dimensionCode: 'resilience', displayName: 'Daya Juang', averageScore: 0, assessmentCount: 0 },
            ]).map((rubric) => {
              const scoreText = rubric.assessmentCount > 0 ? `${rubric.averageScore} / 5.0` : 'Belum Ada Penilaian';
              const percent = rubric.assessmentCount > 0 ? (rubric.averageScore / 5) * 100 : 0;
              return (
                <div
                  key={rubric.dimensionCode}
                  className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2 flex flex-col justify-between"
                >
                  <div className="space-y-1">
                    <span className="text-xs font-bold text-slate-800">{rubric.displayName}</span>
                    <p className="text-lg font-extrabold text-growth-700">{scoreText}</p>
                  </div>
                  <div className="space-y-1.5">
                    <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-growth-600 h-full rounded-full transition-all duration-500"
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                    <p className="text-[10px] text-slate-500">
                      {rubric.assessmentCount > 0
                        ? `Berdasarkan ${rubric.assessmentCount} asesmen guru`
                        : 'Menunggu validasi karya'}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
