'use client';

import React, { useEffect, useState } from 'react';
import { AppShell } from '../../components/layout/AppShell';
import { MetricCard } from '../../components/common/MetricCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { TagChip } from '../../components/common/TagChip';
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
  ShieldCheck,
  Calendar,
  ChevronRight,
  ExternalLink,
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

  const pendingCount = queueItems.filter((i) => i.status === 'submitted').length;
  const revisionCount = queueItems.filter((i) => i.status === 'revision_requested').length;
  const approvedMonthCount = queueItems.filter((i) => i.status === 'approved').length;
  const submittedQueue = queueItems.filter((i) => i.status === 'submitted').slice(0, 4);

  return (
    <AppShell pageTitle="Dashboard Validator Guru" expectedRole="teacher">
      <div className="space-y-6">
        {/* Welcome Banner */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-growth-50 text-growth-700 border border-growth-200">
                Validator Kejuruan & Karakter
              </span>
              <span className="text-xs text-slate-400">• {user?.title}</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Selamat bertugas, {user?.name.split(',')[0]} 👨‍🏫
            </h2>
            <p className="text-sm text-slate-600 max-w-xl leading-relaxed">
              Tinjau pengajuan karya nyata siswa bimbingan Anda, lakukan penilaian rubrik karakter, dan berikan masukan perbaikan yang konstruktif.
            </p>
          </div>

          <div className="shrink-0">
            <Link
              href="/teacher/reviews"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-growth-600 hover:bg-growth-700 text-white font-semibold text-sm transition-all shadow-xs"
            >
              <Inbox className="w-4 h-4" />
              <span>Buka Antrean Validasi ({pendingCount})</span>
            </Link>
          </div>
        </div>

        {/* Overview Metric Cards */}
        {isLoading ? (
          <LoadingSkeleton rows={2} />
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              label="Menunggu Review"
              value={pendingCount}
              subtext="Perlu validasi guru"
              icon={Clock}
              colorScheme="brand"
              badge="Prioritas"
            />
            <MetricCard
              label="Perlu Tindak Lanjut"
              value={revisionCount}
              subtext="Karya dalam masa revisi"
              icon={Inbox}
              colorScheme="revision"
            />
            <MetricCard
              label="Disetujui Bulan Ini"
              value={approvedMonthCount}
              subtext="Tervalidasi resmi"
              icon={CheckCircle2}
              colorScheme="endorse"
            />
            <MetricCard
              label="Siswa Aktif Terbimbing"
              value={36}
              subtext="Kelas XII RPL 1"
              icon={Users}
              colorScheme="growth"
            />
          </div>
        )}

        {/* Approval Queue Preview */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Antrean Karya Perlu Ditinjau</h3>
              <p className="text-xs text-slate-500">
                Pengajuan karya terbaru dari siswa yang menunggu penilaian validator
              </p>
            </div>
            <Link
              href="/teacher/reviews"
              className="text-xs font-semibold text-growth-700 hover:text-growth-800 flex items-center gap-1"
            >
              <span>Buka Semua Antrean</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {submittedQueue.length === 0 ? (
            <div className="p-8 text-center border border-dashed border-slate-200 rounded-xl">
              <CheckCircle2 className="w-8 h-8 text-endorse-500 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-800">Semua Pengajuan Telah Ditinjau!</p>
              <p className="text-xs text-slate-500 mt-0.5">Tidak ada antrean tertunda saat ini.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {submittedQueue.map((item) => (
                <div
                  key={item.id}
                  className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/70 px-2 rounded-xl transition-colors"
                >
                  <div className="space-y-1.5 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-bold text-slate-900">{item.studentName}</span>
                      <span className="text-xs text-slate-400">({item.studentClass})</span>
                      <span className="text-xs text-slate-300">•</span>
                      <span className="text-[11px] text-slate-500">{item.date}</span>
                    </div>

                    <Link
                      href={`/teacher/reviews/${item.id}`}
                      className="text-sm font-bold text-slate-900 hover:text-growth-700 truncate block"
                    >
                      {item.title}
                    </Link>

                    <div className="flex flex-wrap gap-1">
                      {item.tags.map((t) => (
                        <TagChip key={t} label={t} size="sm" />
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-center shrink-0">
                    <Link
                      href={`/teacher/reviews/${item.id}`}
                      className="px-3.5 py-1.5 rounded-lg bg-growth-600 hover:bg-growth-700 text-white text-xs font-semibold transition-colors shadow-2xs flex items-center gap-1"
                    >
                      <span>Tinjau</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Validation Activity Feed */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4">
          <div className="pb-3 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900">Aktivitas Validasi Terakhir</h3>
            <p className="text-xs text-slate-500">Log keputusan validasi dan umpan balik pembimbing</p>
          </div>

          <div className="space-y-3">
            {queueItems
              .filter((i) => i.status !== 'draft' && i.status !== 'submitted')
              .slice(0, 3)
              .map((item) => (
                <div
                  key={item.id}
                  className="p-3.5 rounded-xl border border-slate-100 bg-slate-50/60 flex items-start justify-between gap-3 text-xs"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <StatusBadge status={item.status} size="sm" />
                      <span className="font-semibold text-slate-900 truncate">{item.title}</span>
                    </div>
                    <p className="text-slate-600">
                      Siswa: <strong>{item.studentName}</strong> • Catatan:{' '}
                      <span className="italic">{item.teacherFeedback || 'Validasi sukses.'}</span>
                    </p>
                  </div>
                  <span className="text-[11px] text-slate-400 shrink-0">{item.date}</span>
                </div>
              ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
