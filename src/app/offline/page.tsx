'use client';

import React from 'react';
import Link from 'next/link';
import { WifiOff, RefreshCw, Home } from 'lucide-react';

export default function OfflinePage() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 p-8 text-center shadow-xs">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 text-slate-500 flex items-center justify-center mx-auto mb-4 border border-slate-200">
          <WifiOff className="w-7 h-7" />
        </div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">Koneksi Internet Terputus</h1>
        <p className="text-sm text-slate-600 mt-2 mb-6 leading-relaxed">
          TALENTRA.ID tidak dapat memuat data terbaru karena Anda sedang luring (offline). Silakan periksa koneksi internet Anda dan coba kembali.
        </p>

        <div className="space-y-2.5">
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-semibold text-sm transition-colors shadow-xs"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Muat Ulang Halaman</span>
          </button>

          <Link
            href="/"
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium text-sm transition-colors"
          >
            <Home className="w-4 h-4" />
            <span>Ke Beranda Tersimpan</span>
          </Link>
        </div>

        <p className="text-[11px] text-slate-400 mt-6">
          Sistem PWA TALENTRA.ID melindungi kerahasiaan data siswa dan tidak menyimpan cache data pribadi saat offline.
        </p>
      </div>
    </div>
  );
}
