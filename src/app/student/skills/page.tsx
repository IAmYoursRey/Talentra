'use client';

import React, { useEffect, useState } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { SkillRadarChart } from '../../../components/charts/SkillRadarChart';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';
import { skillService } from '../../../services/skill.service';
import { SkillSnapshot } from '../../../types/skill.types';
import { ShieldCheck, Radar, BarChart2 } from 'lucide-react';

interface EvidenceStrengthItem {
  skill: string;
  count: number;
  percentage: number;
}

export default function StudentSkillsPage() {
  const [snapshot, setSnapshot] = useState<SkillSnapshot | null>(() => skillService.getCachedSkillSnapshot());
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let active = true;
    const loadSkillData = async () => {
      const data = await skillService.getStudentSkillSnapshot();
      if (active) {
        setSnapshot(data);
      }
    };

    loadSkillData();
    return () => {
      active = false;
    };
  }, []);

  const strengths: EvidenceStrengthItem[] = [
    { skill: 'Web Development', count: 11, percentage: 92 },
    { skill: 'Problem Solving', count: 9, percentage: 75 },
    { skill: 'Leadership', count: 7, percentage: 58 },
    { skill: 'Communication', count: 6, percentage: 50 },
    { skill: 'Creativity', count: 5, percentage: 42 },
    { skill: 'Teamwork', count: 4, percentage: 33 },
  ];

  return (
    <AppShell pageTitle="Skill Map" expectedRole="student" isPageLoading={isLoading}>
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header matching 09-Student-SkillMap-HF.svg */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              Skill Map
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Peta kemampuan hanya dari karya yang sudah divalidasi guru.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FAF5FF] border border-[#E9E1F4] text-[#A78BFA] font-bold text-xs shadow-xs self-start sm:self-auto">
            <span>Semester 5</span>
          </div>
        </div>

        {/* 2-Column Grid: Radar & Evidence Strength */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Radar Kemampuan (7 cols) */}
          <div className="lg:col-span-7 bg-white rounded-[18px] border border-[#E9E1F4] p-6 sm:p-8 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-extrabold text-[#261331]">Radar kemampuan</h2>
                  <p className="text-xs text-[#6F607D] mt-0.5">
                    12 evidence tervalidasi • 8 skill terpetakan
                  </p>
                </div>
              </div>

              {isLoading ? (
                <LoadingSkeleton rows={5} />
              ) : (
                <div className="py-4">
                  <SkillRadarChart data={snapshot?.radarPoints || []} height={340} />
                </div>
              )}
            </div>
          </div>

          {/* Kekuatan Evidence (5 cols) */}
          <div className="lg:col-span-5 bg-white rounded-[18px] border border-[#E9E1F4] p-6 sm:p-8 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between">
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-extrabold text-[#261331]">Kekuatan evidence</h2>
                <p className="text-xs text-[#6F607D] mt-0.5">
                  Jumlah karya tervalidasi per skill
                </p>
              </div>

              <div className="space-y-4">
                {strengths.map((item) => (
                  <div key={item.skill} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[#261331]">{item.skill}</span>
                      <span className="font-extrabold text-[#6D28D9]">{item.count} karya</span>
                    </div>
                    <div className="w-full h-2.5 rounded-full bg-[#F3E8FF] overflow-hidden">
                      <div
                        className="h-full rounded-full tal-btn-primary transition-all duration-500"
                        style={{ width: `${item.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Banner matching 09-Student-SkillMap-HF.svg */}
        <div className="p-4 rounded-xl bg-[#F7F2FF] border border-purple-100 text-center">
          <p className="text-xs font-bold text-[#6D28D9]">
            APPROVED ONLY — draft, pending, dan rejected tidak memengaruhi Skill Map.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
