'use client';

import React, { useEffect, useState } from 'react';
import { AppShell } from '../../components/layout/AppShell';
import { MetricCard } from '../../components/common/MetricCard';
import { LoadingSkeleton } from '../../components/common/LoadingSkeleton';
import { reviewService } from '../../services/review.service';
import { authService } from '../../services/auth.service';
import { PortfolioItem } from '../../types/portfolio.types';
import { UserProfile } from '../../types/auth.types';
import {
  Inbox,
  Clock,
  CheckCircle2,
  Users,
  ArrowRight,
  School,
  ChevronRight,
} from 'lucide-react';
import Link from 'next/link';

export default function TeacherDashboardPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [queueItems, setQueueItems] = useState<PortfolioItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchTeacherData = async () => {
    const session = await authService.getCurrentSession();
    setUser(session.user);

    const items = await reviewService.getReviewQueue();
    setQueueItems(items);
    setIsLoading(false);
  };

  useEffect(() => {
    fetchTeacherData();
    const unsub = reviewService.subscribeQueue(fetchTeacherData);
    return unsub;
  }, []);

  const priorityQueue = [
    {
      id: 'p-1',
      initials: 'DP',
      name: 'Dimas Pratama',
      project: 'Waste2Wisdom',
      class: 'XII IPA 2',
    },
    {
      id: 'p-2',
      initials: 'NK',
      name: 'Nabila K.',
      project: 'Video Kampanye',
      class: 'XI IPA 1',
    },
    {
      id: 'p-3',
      initials: 'AF',
      name: 'Arya F.',
      project: 'Robot Line Follower',
      class: 'XII IPA 1',
    },
    {
      id: 'p-4',
      initials: 'SA',
      name: 'Salsa A.',
      project: 'Festival Seni',
      class: 'XI IPA 2',
    },
  ];

  const assignedClasses = [
    { name: 'X IPA 1', students: 31, pending: 4 },
    { name: 'XI IPA 2', students: 30, pending: 5 },
    { name: 'XII IPA 2', students: 31, pending: 9 },
  ];

  return (
    <AppShell pageTitle="Dashboard" expectedRole="teacher" isPageLoading={isLoading}>
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header matching 12-Teacher-Dashboard-HF.svg */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              Teacher Dashboard
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Ringkasan antrean validasi, kelas, dan progres siswa.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FAF5FF] border border-[#E9E1F4] text-[#A78BFA] font-bold text-xs shadow-xs self-start sm:self-auto">
            <Clock className="w-3.5 h-3.5" />
            <span>18 menunggu</span>
          </div>
        </div>

        {/* 3 Metric Cards matching 12-Teacher-Dashboard-HF.svg */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6">
          <MetricCard
            indexNumber={1}
            label="Menunggu review"
            value="18"
            subtext="+5 hari ini"
            icon={Inbox}
            href="/teacher/reviews"
          />
          <MetricCard
            indexNumber={2}
            label="Sudah direview"
            value="146"
            subtext="semester ini"
            icon={CheckCircle2}
            href="/teacher/history"
          />
          <MetricCard
            indexNumber={3}
            label="Kelas aktif"
            value="3"
            subtext="92 siswa"
            icon={School}
            href="/teacher/classes"
          />
        </div>

        {/* 2-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Prioritas Approval Queue (7 cols) */}
          <div className="lg:col-span-7 bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between">
            <div>
              <div className="mb-4">
                <h2 className="text-lg font-extrabold text-[#261331]">Prioritas Approval Queue</h2>
                <p className="text-xs text-[#6F607D] mt-0.5">
                  Urut berdasarkan waktu masuk
                </p>
              </div>

              <div className="space-y-3">
                {isLoading ? (
                  <LoadingSkeleton rows={3} />
                ) : (
                  priorityQueue.map((item) => (
                    <div
                      key={item.id}
                      className="p-3.5 rounded-2xl bg-[#FCFBFF] border border-[#E9E1F4] flex items-center justify-between gap-4 hover:border-purple-300 transition-all"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-9 h-9 rounded-full bg-purple-100 text-[#6D28D9] font-black text-xs flex items-center justify-center shrink-0">
                          {item.initials}
                        </div>
                        <div className="min-w-0">
                          <h3 className="text-sm font-extrabold text-[#261331] truncate">
                            {item.name}
                          </h3>
                          <p className="text-xs text-[#6F607D] truncate">
                            {item.project} • {item.class}
                          </p>
                        </div>
                      </div>

                      <Link
                        href={`/teacher/reviews/${item.id}`}
                        className="px-4 py-1.5 rounded-xl tal-btn-primary font-bold text-xs shrink-0 shadow-xs"
                      >
                        Review
                      </Link>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="pt-6 border-t border-[#E9E1F4] mt-6 flex justify-end">
              <Link
                href="/teacher/reviews"
                className="text-xs font-bold text-[#6D28D9] hover:text-[#8B5CF6] inline-flex items-center gap-1.5"
              >
                <span>Buka semua antrean</span>
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Right Column: Kelas Saya (5 cols) */}
          <div className="lg:col-span-5 bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between">
            <div>
              <div className="mb-4">
                <h2 className="text-lg font-extrabold text-[#261331]">Kelas Saya</h2>
                <p className="text-xs text-[#6F607D] mt-0.5">
                  Assignment validator aktif
                </p>
              </div>

              <div className="space-y-3">
                {assignedClasses.map((cls) => (
                  <div
                    key={cls.name}
                    className="p-4 rounded-xl bg-[#FCFBFF] border border-[#E9E1F4] flex items-center justify-between"
                  >
                    <div>
                      <h3 className="text-sm font-extrabold text-[#261331]">{cls.name}</h3>
                      <p className="text-xs text-[#6F607D] mt-0.5">{cls.students} siswa</p>
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#FAF5FF] text-[#A78BFA] border border-purple-100">
                      {cls.pending} pending
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-6 border-t border-[#E9E1F4] mt-6 flex justify-end">
              <Link
                href="/teacher/classes"
                className="text-xs font-bold text-[#6D28D9] hover:text-[#8B5CF6] inline-flex items-center gap-1.5"
              >
                <span>Lihat kelas</span>
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
