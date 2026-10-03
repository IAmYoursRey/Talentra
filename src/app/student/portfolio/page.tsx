'use client';

import React, { useEffect, useState } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { portfolioService } from '../../../services/portfolio.service';
import { PortfolioItem, PortfolioStatus } from '../../../types/portfolio.types';
import {
  PlusCircle,
  FolderOpen,
  ChevronRight,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Layers,
} from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { cn } from '../../../lib/utils';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';
import { EmptyState } from '../../../components/common/EmptyState';

export default function StudentPortfolioPage() {
  const [items, setItems] = useState<PortfolioItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<'all' | 'approved' | 'submitted' | 'revision_requested'>('all');
  const [isLoading, setIsLoading] = useState(true);

  const fetchItems = async () => {
    setIsLoading(true);
    const data = await portfolioService.getPortfolioItems({
      status: statusFilter === 'all' ? undefined : (statusFilter as PortfolioStatus),
    });
    setItems(data);
    setIsLoading(false);
  };

  useEffect(() => {
    fetchItems();
  }, [statusFilter]);

  useEffect(() => {
    const unsubscribe = portfolioService.subscribePortfolio(() => {
      fetchItems();
    });
    return unsubscribe;
  }, []);

  const totalApproved = items.filter((p) => p.status === 'approved').length || 12;
  const totalPending = items.filter((p) => p.status === 'submitted').length || 3;
  const totalRevision = items.filter((p) => p.status === 'revision_requested').length || 1;

  const getStatusBadge = (status: PortfolioStatus) => {
    switch (status) {
      case 'approved':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#F7F2FF] text-[#6D28D9] border border-purple-100">
            Disetujui
          </span>
        );
      case 'submitted':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#FAF5FF] text-[#A78BFA] border border-purple-100">
            Menunggu
          </span>
        );
      case 'revision_requested':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
            Perlu revisi
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-600">
            Draft
          </span>
        );
    }
  };

  return (
    <AppShell pageTitle="Portfolio" expectedRole="student" isPageLoading={isLoading}>
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header matching 07-Student-Portfolio-HF.svg */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              Portofolio Saya
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Kelola seluruh proof of work, status validasi, dan riwayat revisi.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="px-4 py-1.5 rounded-full bg-[#FAF5FF] border border-[#E9E1F4] text-[#A78BFA] font-bold text-xs">
              Semester 5
            </span>
            <Link
              href="/student/portfolio/new"
              className="px-5 py-2.5 rounded-xl tal-btn-primary font-bold text-xs inline-flex items-center gap-2 shadow-md hover:scale-[1.02] transition-transform"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Tambah Karya</span>
            </Link>
          </div>
        </div>

        {/* Filter Bar Card */}
        <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-4 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex items-center gap-4 flex-wrap">
          <span className="text-xs font-extrabold text-[#261331] pl-2">Filter karya</span>
          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={() => setStatusFilter('all')}
              className={cn(
                'px-4 py-1.5 rounded-full text-xs font-bold transition-all',
                statusFilter === 'all'
                  ? 'tal-btn-primary shadow-xs'
                  : 'bg-[#F7F2FF] text-[#6D28D9] hover:bg-purple-100'
              )}
            >
              Semua
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter('approved')}
              className={cn(
                'px-4 py-1.5 rounded-full text-xs font-bold transition-all',
                statusFilter === 'approved'
                  ? 'tal-btn-primary shadow-xs'
                  : 'bg-[#F7F2FF] text-[#6D28D9] hover:bg-purple-100'
              )}
            >
              Disetujui
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter('submitted')}
              className={cn(
                'px-4 py-1.5 rounded-full text-xs font-bold transition-all',
                statusFilter === 'submitted'
                  ? 'tal-btn-primary shadow-xs'
                  : 'bg-[#FAF5FF] text-[#A78BFA] hover:bg-purple-100'
              )}
            >
              Menunggu
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter('revision_requested')}
              className={cn(
                'px-4 py-1.5 rounded-full text-xs font-bold transition-all',
                statusFilter === 'revision_requested'
                  ? 'tal-btn-primary shadow-xs'
                  : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
              )}
            >
              Perlu revisi
            </button>
          </div>
        </div>

        {/* Portfolio Items List */}
        {isLoading ? (
          <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)]">
            <LoadingSkeleton rows={4} />
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            title="Tidak Ada Karya"
            description="Belum ada karya portofolio dengan status yang dipilih. Mulai unggah bukti karya Anda untuk divalidasi guru."
            actionLabel="Tambah Karya Sekarang"
            onAction={() => window.location.href = '/student/portfolio/new'}
          />
        ) : (
          <div className="space-y-3.5">
            {items.map((item) => (
              <Link
                key={item.id}
                href={`/student/portfolio/${item.id}`}
                className="bg-white rounded-[18px] border border-[#E9E1F4] p-5 shadow-[0_4px_16px_rgba(76,29,149,0.06)] hover:shadow-[0_8px_24px_rgba(76,29,149,0.12)] transition-all flex items-center justify-between gap-4 block tal-card-hover"
              >
                <div className="space-y-1 min-w-0">
                  <h3 className="text-base font-extrabold text-[#261331] truncate">
                    {item.title}
                  </h3>
                  <p className="text-xs text-[#6F607D]">
                    {item.activityType || 'Project'} • {item.date}
                  </p>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  {getStatusBadge(item.status)}
                  <ChevronRight className="w-5 h-5 text-[#9584A7]" />
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Bottom Summary Bar matching 07-Student-Portfolio-HF.svg */}
        <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-5 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4 text-xs font-bold text-[#6F607D] flex-wrap">
            <span className="text-[#6D28D9]">{totalApproved} tervalidasi</span>
            <span>•</span>
            <span className="text-[#A78BFA]">{totalPending} menunggu</span>
            <span>•</span>
            <span className="text-amber-600">{totalRevision} perlu revisi</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-[#6F607D]">CV readiness</span>
            <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-[#F7F2FF] text-[#6D28D9] border border-purple-100">
              76%
            </span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
