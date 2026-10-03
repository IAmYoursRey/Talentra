'use client';

import React, { useState } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { CheckCircle2, Clock, Filter, AlertCircle, RotateCcw, XCircle } from 'lucide-react';
import { cn } from '../../../lib/utils';

interface HistoryItem {
  id: string;
  date: string;
  studentName: string;
  projectTitle: string;
  status: 'endorsed' | 'revision' | 'rejected';
}

export default function TeacherHistoryPage() {
  const [activeFilter, setActiveFilter] = useState<'all' | 'endorsed' | 'revision' | 'rejected'>('all');

  const historyItems: HistoryItem[] = [
    {
      id: 'h-1',
      date: '12 Sep 2026',
      studentName: 'Raihan Ansari',
      projectTitle: 'Waste2Wisdom',
      status: 'endorsed',
    },
    {
      id: 'h-2',
      date: '11 Sep 2026',
      studentName: 'Nabila K.',
      projectTitle: 'Video Kampanye',
      status: 'revision',
    },
    {
      id: 'h-3',
      date: '10 Sep 2026',
      studentName: 'Arya F.',
      projectTitle: 'Robot Line Follower',
      status: 'endorsed',
    },
    {
      id: 'h-4',
      date: '09 Sep 2026',
      studentName: 'Salsa A.',
      projectTitle: 'Poster Festival',
      status: 'rejected',
    },
  ];

  const filteredItems = historyItems.filter((item) => {
    if (activeFilter === 'all') return true;
    return item.status === activeFilter;
  });

  const getStatusBadge = (status: HistoryItem['status']) => {
    switch (status) {
      case 'endorsed':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#F7F2FF] text-[#6D28D9] border border-purple-100">
            Endorsed
          </span>
        );
      case 'revision':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#FAF5FF] text-[#A78BFA] border border-purple-100">
            Revisi
          </span>
        );
      case 'rejected':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-600 border border-rose-100">
            Rejected
          </span>
        );
    }
  };

  return (
    <AppShell pageTitle="Riwayat Validasi" expectedRole="teacher">
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              Riwayat Validasi
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Audit trail keputusan review dan feedback guru.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FAF5FF] border border-[#E9E1F4] text-[#A78BFA] font-bold text-xs shadow-xs self-start sm:self-auto">
            <Clock className="w-3.5 h-3.5" />
            <span>18 menunggu</span>
          </div>
        </div>

        {/* Filter Card */}
        <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-4 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex items-center gap-4 flex-wrap">
          <span className="text-xs font-extrabold text-[#261331] pl-2">Filter</span>
          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={() => setActiveFilter('all')}
              className={cn(
                'px-4 py-1.5 rounded-full text-xs font-bold transition-all',
                activeFilter === 'all'
                  ? 'tal-btn-primary shadow-xs'
                  : 'bg-[#F7F2FF] text-[#6D28D9] hover:bg-purple-100'
              )}
            >
              Semua
            </button>
            <button
              type="button"
              onClick={() => setActiveFilter('endorsed')}
              className={cn(
                'px-4 py-1.5 rounded-full text-xs font-bold transition-all',
                activeFilter === 'endorsed'
                  ? 'tal-btn-primary shadow-xs'
                  : 'bg-[#F7F2FF] text-[#6D28D9] hover:bg-purple-100'
              )}
            >
              Endorsed
            </button>
            <button
              type="button"
              onClick={() => setActiveFilter('revision')}
              className={cn(
                'px-4 py-1.5 rounded-full text-xs font-bold transition-all',
                activeFilter === 'revision'
                  ? 'tal-btn-primary shadow-xs'
                  : 'bg-[#FAF5FF] text-[#A78BFA] hover:bg-purple-100'
              )}
            >
              Revisi
            </button>
            <button
              type="button"
              onClick={() => setActiveFilter('rejected')}
              className={cn(
                'px-4 py-1.5 rounded-full text-xs font-bold transition-all',
                activeFilter === 'rejected'
                  ? 'tal-btn-primary shadow-xs'
                  : 'bg-[#F6F1FF] text-[#6D28D9] hover:bg-purple-100'
              )}
            >
              Rejected
            </button>
          </div>
        </div>

        {/* History Table Card */}
        <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 shadow-[0_4px_16px_rgba(76,29,149,0.06)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#FDFBFF] rounded-xl text-xs font-bold text-[#6F607D]">
                  <th className="py-3 px-4 rounded-l-xl">Tanggal</th>
                  <th className="py-3 px-4">Siswa</th>
                  <th className="py-3 px-4">Karya</th>
                  <th className="py-3 px-4 rounded-r-xl">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E9E1F4] text-xs">
                {filteredItems.map((item) => (
                  <tr key={item.id} className="hover:bg-purple-50/20 transition-colors">
                    <td className="py-4 px-4 font-semibold text-[#261331]">{item.date}</td>
                    <td className="py-4 px-4 font-semibold text-[#261331]">{item.studentName}</td>
                    <td className="py-4 px-4 font-medium text-[#261331]">{item.projectTitle}</td>
                    <td className="py-4 px-4">{getStatusBadge(item.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Footer Note */}
          <div className="mt-8 p-3 rounded-xl bg-[#FDFBFF] text-center border border-[#E9E1F4]">
            <p className="text-xs font-semibold text-[#6F607D]">
              Perubahan keputusan tidak menghapus catatan sebelumnya.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
