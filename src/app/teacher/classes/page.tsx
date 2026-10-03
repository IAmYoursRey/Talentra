'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AppShell } from '../../../components/layout/AppShell';
import { reviewService } from '../../../services/review.service';
import { ArrowRight, School, Users, Clock, ShieldCheck, CheckCircle2 } from 'lucide-react';

interface AssignedClass {
  id: string;
  name: string;
  grade: string;
  studentCount: number;
  pendingCount: number;
  description: string;
}

export default function TeacherClassesPage() {
  const router = useRouter();
  const [classes, setClasses] = useState<AssignedClass[]>([
    {
      id: 'cls-x-ipa-1',
      name: 'X IPA 1',
      grade: 'X',
      studentCount: 31,
      pendingCount: 4,
      description: 'Lihat siswa, karya pending, dan riwayat validasi kelas.',
    },
    {
      id: 'cls-xi-ipa-2',
      name: 'XI IPA 2',
      grade: 'XI',
      studentCount: 30,
      pendingCount: 5,
      description: 'Lihat siswa, karya pending, dan riwayat validasi kelas.',
    },
    {
      id: 'cls-xii-ipa-2',
      name: 'XII IPA 2',
      grade: 'XII',
      studentCount: 31,
      pendingCount: 9,
      description: 'Lihat siswa, karya pending, dan riwayat validasi kelas.',
    },
  ]);

  const totalPending = classes.reduce((acc, c) => acc + c.pendingCount, 0);

  return (
    <AppShell pageTitle="Kelas Saya" expectedRole="teacher">
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header matching 14-Teacher-Classes-HF.svg */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              Kelas Saya
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Kelola ruang validasi berdasarkan kelas yang ditugaskan.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FAF5FF] border border-[#E9E1F4] text-[#A78BFA] font-bold text-xs shadow-xs self-start sm:self-auto">
            <Clock className="w-3.5 h-3.5" />
            <span>{totalPending} menunggu</span>
          </div>
        </div>

        {/* Class Cards */}
        <div className="space-y-4">
          {classes.map((cls, idx) => (
            <div
              key={cls.id}
              className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] hover:shadow-[0_8px_24px_rgba(76,29,149,0.12)] transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#F3E8FF] to-[#FAF5FF] border border-purple-200 flex items-center justify-center font-extrabold text-base text-[#6D28D9] shrink-0">
                  {idx + 1}
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-extrabold text-[#261331] tracking-tight">
                      {cls.name}
                    </h2>
                    <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-[#6F607D]">
                      {cls.studentCount} siswa
                    </span>
                  </div>
                  <p className="text-xs text-[#6F607D] mt-2">
                    {cls.description}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 self-end md:self-auto shrink-0">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#F3E8FF] text-[#6D28D9] border border-purple-100">
                  {cls.pendingCount} menunggu
                </span>
                <Link
                  href={`/teacher/reviews?class=${encodeURIComponent(cls.name)}`}
                  className="px-6 py-2.5 rounded-xl tal-btn-primary font-bold text-xs inline-flex items-center gap-2 shadow-md"
                >
                  <span>Buka</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>

        {/* Assignment Policy Info Card */}
        <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-5 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex items-center gap-4">
          <div className="w-9 h-9 rounded-xl bg-purple-100 text-[#6D28D9] flex items-center justify-center shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-xs font-extrabold text-[#261331]">Assignment validator</h3>
            <p className="text-[11px] text-[#6F607D] mt-0.5">
              Hanya kelas yang ditugaskan admin yang muncul di dashboard guru.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
