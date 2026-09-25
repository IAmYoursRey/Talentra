'use client';

import React, { useEffect, useState } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { StatusBadge } from '../../../components/common/StatusBadge';
import { TagChip } from '../../../components/common/TagChip';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';
import { EmptyState } from '../../../components/common/EmptyState';
import { reviewService } from '../../../services/review.service';
import { PortfolioItem, PortfolioStatus } from '../../../types/portfolio.types';
import {
  Search,
  SlidersHorizontal,
  ArrowUpDown,
  Inbox,
  FileText,
  Link as LinkIcon,
  ChevronRight,
  User,
} from 'lucide-react';
import Link from 'next/link';

export default function TeacherReviewQueuePage() {
  const [items, setItems] = useState<PortfolioItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [classFilter, setClassFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState<PortfolioStatus | 'all'>('submitted');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest'>('newest');

  const fetchQueue = async () => {
    setIsLoading(true);
    const data = await reviewService.getReviewQueue({
      search,
      className: classFilter,
      status: statusFilter,
      sortBy,
    });
    setItems(data);
    setIsLoading(false);
  };

  useEffect(() => {
    fetchQueue();
  }, [search, classFilter, statusFilter, sortBy]);

  useEffect(() => {
    const unsub = reviewService.subscribeQueue(fetchQueue);
    return unsub;
  }, []);

  return (
    <AppShell pageTitle="Antrean Validasi Guru" expectedRole="teacher">
      <div className="space-y-6">
        {/* Header Title */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
              Antrean Validasi Portofolio (Intelligent Inbox)
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Daftar karya nyata siswa yang menunggu asesmen, tinjauan bukti, dan penilaian rubrik karakter.
            </p>
          </div>
          <span className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-growth-50 text-growth-700 border border-growth-200 self-start sm:self-center">
            {items.length} Pengajuan Ditemukan
          </span>
        </div>

        {/* Search & Filters */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs space-y-3">
          <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Cari siswa, judul karya, atau tag kompetensi..."
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-growth-500 transition-colors"
              />
            </div>

            {/* Class Filter */}
            <div className="flex items-center gap-2">
              <select
                value={classFilter}
                onChange={(e) => setClassFilter(e.target.value)}
                className="px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-growth-500"
              >
                <option value="all">Semua Rombel/Kelas</option>
                <option value="XII RPL 1">XII RPL 1</option>
                <option value="XII RPL 2">XII RPL 2</option>
                <option value="XI DKV 2">XI DKV 2</option>
                <option value="XII TKJ 1">XII TKJ 1</option>
              </select>

              <button
                type="button"
                onClick={() => setSortBy(sortBy === 'newest' ? 'oldest' : 'newest')}
                className="px-3 py-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-xs font-semibold text-slate-700 flex items-center gap-1.5 transition-colors shrink-0"
              >
                <ArrowUpDown className="w-3.5 h-3.5" />
                <span>{sortBy === 'newest' ? 'Terbaru' : 'Terlama'}</span>
              </button>
            </div>
          </div>

          {/* Status Tabs */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-1 text-xs">
            <span className="text-slate-400 text-xs flex items-center gap-1 shrink-0 font-medium">
              <SlidersHorizontal className="w-3 h-3" />
              <span>Status:</span>
            </span>

            {[
              { id: 'submitted', label: 'Menunggu Validasi' },
              { id: 'revision_requested', label: 'Perlu Revisi' },
              { id: 'approved', label: 'Telah Disetujui' },
              { id: 'rejected', label: 'Ditolak' },
              { id: 'all', label: 'Semua Status' },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setStatusFilter(tab.id as any)}
                className={`px-3 py-1 rounded-full border text-xs font-medium whitespace-nowrap transition-colors ${
                  statusFilter === tab.id
                    ? 'bg-growth-600 text-white border-growth-600 shadow-2xs font-semibold'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Inbox Table/List */}
        {isLoading ? (
          <div className="bg-white p-8 rounded-2xl border border-slate-200">
            <LoadingSkeleton rows={5} />
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="Tidak Ada Antrean Validasi"
            description="Tidak ada pengajuan portofolio yang cocok dengan kriteria filter saat ini."
          />
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200/80 divide-y divide-slate-100 shadow-xs overflow-hidden">
            {items.map((item) => (
              <div
                key={item.id}
                className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/70 transition-colors group"
              >
                {/* Left info */}
                <div className="space-y-1.5 min-w-0 flex-1">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <StatusBadge status={item.status} size="sm" />
                    <span className="text-xs font-bold text-slate-900 flex items-center gap-1">
                      <User className="w-3.5 h-3.5 text-slate-400" />
                      <span>{item.studentName}</span>
                    </span>
                    <span className="text-xs text-slate-400">({item.studentClass})</span>
                    <span className="text-xs text-slate-300">•</span>
                    <span className="text-xs text-slate-400">{item.date}</span>
                  </div>

                  <Link
                    href={`/teacher/reviews/${item.id}`}
                    className="text-base font-bold text-slate-900 group-hover:text-growth-700 truncate block transition-colors"
                  >
                    {item.title}
                  </Link>

                  <p className="text-xs text-slate-600 line-clamp-1 max-w-3xl">
                    {item.description}
                  </p>

                  <div className="flex items-center gap-3 pt-1 flex-wrap text-xs text-slate-500">
                    <div className="flex items-center gap-1">
                      {item.evidence.type === 'file' ? (
                        <>
                          <FileText className="w-3.5 h-3.5 text-red-500" />
                          <span className="text-[11px] truncate max-w-[140px]">
                            {item.evidence.fileName || 'Berkas Dokumen'}
                          </span>
                        </>
                      ) : (
                        <>
                          <LinkIcon className="w-3.5 h-3.5 text-brand-500" />
                          <span className="text-[11px] truncate max-w-[140px]">Tautan Publik</span>
                        </>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-1">
                      {item.tags.map((t) => (
                        <TagChip key={t} label={t} size="sm" />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right Action */}
                <div className="flex items-center gap-2 shrink-0 self-start sm:self-center">
                  <Link
                    href={`/teacher/reviews/${item.id}`}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-growth-600 hover:bg-growth-700 text-white font-semibold text-xs transition-colors shadow-2xs"
                  >
                    <span>{item.status === 'submitted' ? 'Validasi Karya' : 'Lihat Detail'}</span>
                    <ChevronRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
