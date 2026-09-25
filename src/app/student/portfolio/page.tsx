'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { StatusBadge } from '../../../components/common/StatusBadge';
import { TagChip } from '../../../components/common/TagChip';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';
import { EmptyState } from '../../../components/common/EmptyState';
import { portfolioService } from '../../../services/portfolio.service';
import { PortfolioItem, PortfolioStatus, ActivityType } from '../../../types/portfolio.types';
import {
  PlusCircle,
  Search,
  SlidersHorizontal,
  LayoutGrid,
  List,
  FolderOpen,
  ArrowUpDown,
  FileText,
  Link as LinkIcon,
  ChevronRight,
} from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function StudentPortfolioPage() {
  const router = useRouter();
  const [items, setItems] = useState<PortfolioItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<PortfolioStatus | 'all'>('all');
  const [activityFilter, setActivityFilter] = useState<ActivityType | 'all'>('all');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest'>('newest');
  const [viewLayout, setViewLayout] = useState<'grid' | 'list'>('grid');

  const fetchItems = async () => {
    setIsLoading(true);
    const data = await portfolioService.getPortfolioItems({
      search,
      status: statusFilter,
      activityType: activityFilter,
      sortBy,
    });
    setItems(data);
    setIsLoading(false);
  };

  useEffect(() => {
    fetchItems();
  }, [search, statusFilter, activityFilter, sortBy]);

  useEffect(() => {
    const unsubscribe = portfolioService.subscribePortfolio(() => {
      fetchItems();
    });
    return unsubscribe;
  }, []);

  return (
    <AppShell pageTitle="Portofolio Karya" expectedRole="student">
      <div className="space-y-6">
        {/* Top Header & Primary CTA */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
              Koleksi Portofolio Karya
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Daftar seluruh artefak karya, proyek kejuruan, dan rekam jejak yang diajukan.
            </p>
          </div>

          <Link
            href="/student/portfolio/new"
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-sm transition-colors shadow-xs"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Tambah Karya</span>
          </Link>
        </div>

        {/* Search, Filter, and View Controls */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs space-y-3">
          <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Cari karya berdasarkan judul, deskripsi, atau tag..."
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
              />
            </div>

            {/* Layout Toggle & Sort */}
            <div className="flex items-center gap-2 self-end md:self-auto shrink-0">
              <div className="flex items-center border border-slate-200 rounded-xl p-1 bg-slate-50">
                <button
                  type="button"
                  onClick={() => setSortBy(sortBy === 'newest' ? 'oldest' : 'newest')}
                  className="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-700 hover:bg-white flex items-center gap-1.5 transition-colors"
                  title="Ubah Urutan"
                >
                  <ArrowUpDown className="w-3.5 h-3.5" />
                  <span>{sortBy === 'newest' ? 'Terbaru' : 'Terlama'}</span>
                </button>
              </div>

              <div className="flex items-center border border-slate-200 rounded-xl p-1 bg-slate-50">
                <button
                  type="button"
                  onClick={() => setViewLayout('grid')}
                  aria-label="Tampilan Kisi"
                  className={`p-1.5 rounded-lg text-xs transition-colors ${
                    viewLayout === 'grid' ? 'bg-white shadow-2xs text-brand-600' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <LayoutGrid className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setViewLayout('list')}
                  aria-label="Tampilan Daftar"
                  className={`p-1.5 rounded-lg text-xs transition-colors ${
                    viewLayout === 'list' ? 'bg-white shadow-2xs text-brand-600' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <List className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Filter Chips Row */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-1 text-xs">
            <span className="text-slate-400 text-xs flex items-center gap-1 shrink-0 font-medium">
              <SlidersHorizontal className="w-3 h-3" />
              <span>Status:</span>
            </span>

            {[
              { id: 'all', label: 'Semua Status' },
              { id: 'approved', label: 'Disetujui' },
              { id: 'submitted', label: 'Menunggu Validasi' },
              { id: 'revision_requested', label: 'Perlu Revisi' },
              { id: 'draft', label: 'Draft' },
              { id: 'rejected', label: 'Ditolak' },
            ].map((st) => (
              <button
                key={st.id}
                type="button"
                onClick={() => setStatusFilter(st.id as any)}
                className={`px-3 py-1 rounded-full border text-xs font-medium whitespace-nowrap transition-colors ${
                  statusFilter === st.id
                    ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                {st.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content Area */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {Array.from({ length: 3 }).map((_, idx) => (
              <div key={idx} className="bg-white p-6 rounded-2xl border border-slate-200">
                <LoadingSkeleton rows={4} />
              </div>
            ))}
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={FolderOpen}
            title="Tidak Ada Portofolio Ditemukan"
            description="Belum ada karya yang sesuai dengan kriteria pencarian atau filter yang dipilih."
            actionLabel="+ Buat Portofolio Baru"
            onAction={() => router.push('/student/portfolio/new')}
          />
        ) : viewLayout === 'grid' ? (
          /* GRID VIEW */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {items.map((item) => (
              <div
                key={item.id}
                className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs hover:border-slate-300 hover:shadow-sm transition-all flex flex-col justify-between group"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <StatusBadge status={item.status} size="sm" />
                    <span className="text-[11px] text-slate-400">{item.date}</span>
                  </div>

                  <Link href={`/student/portfolio/${item.id}`} className="block group-hover:text-brand-600 transition-colors">
                    <h3 className="text-base font-bold text-slate-900 leading-snug line-clamp-2">
                      {item.title}
                    </h3>
                  </Link>

                  <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                    {item.description}
                  </p>

                  <div className="flex flex-wrap gap-1 pt-1">
                    {item.tags.map((tag) => (
                      <TagChip key={tag} label={tag} size="sm" />
                    ))}
                  </div>
                </div>

                <div className="mt-5 pt-3.5 border-t border-slate-100 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5 text-slate-500">
                    {item.evidence.type === 'file' ? (
                      <>
                        <FileText className="w-3.5 h-3.5 text-red-500" />
                        <span className="text-[11px] truncate max-w-[120px]">
                          {item.evidence.fileName || 'Berkas Lampiran'}
                        </span>
                      </>
                    ) : (
                      <>
                        <LinkIcon className="w-3.5 h-3.5 text-brand-500" />
                        <span className="text-[11px] truncate max-w-[120px]">
                          Tautan Eksternal
                        </span>
                      </>
                    )}
                  </div>

                  <Link
                    href={`/student/portfolio/${item.id}`}
                    className="font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform"
                  >
                    <span>Detail</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* LIST VIEW */
          <div className="bg-white rounded-2xl border border-slate-200/80 divide-y divide-slate-100 shadow-xs overflow-hidden">
            {items.map((item) => (
              <div
                key={item.id}
                className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/70 transition-colors"
              >
                <div className="space-y-1.5 min-w-0 flex-1">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <StatusBadge status={item.status} size="sm" />
                    <span className="text-xs text-slate-400">• {item.date}</span>
                    <span className="text-xs text-slate-500 capitalize bg-slate-100 px-2 py-0.5 rounded">
                      {item.activityType}
                    </span>
                  </div>

                  <Link
                    href={`/student/portfolio/${item.id}`}
                    className="text-base font-bold text-slate-900 hover:text-brand-600 truncate block"
                  >
                    {item.title}
                  </Link>

                  <p className="text-xs text-slate-600 line-clamp-1">
                    {item.description}
                  </p>

                  <div className="flex flex-wrap gap-1 pt-1">
                    {item.tags.map((t) => (
                      <TagChip key={t} label={t} size="sm" />
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 self-start sm:self-center">
                  <Link
                    href={`/student/portfolio/${item.id}`}
                    className="px-3.5 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors"
                  >
                    Lihat Portofolio
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
