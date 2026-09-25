import React from 'react';
import { EvidenceSource } from '../../types/portfolio.types';
import { FileText, Image as ImageIcon, Video, ExternalLink, Github, HardDrive, Globe } from 'lucide-react';
import { cn } from '../../lib/utils';

interface EvidencePreviewProps {
  evidence: EvidenceSource;
  className?: string;
}

export const EvidencePreview: React.FC<EvidencePreviewProps> = ({ evidence, className }) => {
  if (evidence.type === 'link') {
    const isGithub = evidence.url.includes('github.com');
    const isDrive = evidence.url.includes('drive.google.com');

    const Icon = isGithub ? Github : isDrive ? HardDrive : Globe;
    const platformLabel = isGithub ? 'GitHub Repository' : isDrive ? 'Google Drive Folder' : 'Tautan Eksternal';

    return (
      <div
        className={cn(
          'rounded-xl border border-slate-200 bg-slate-50/70 p-4 transition-all hover:bg-slate-100/60',
          className
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-slate-700 shrink-0">
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
                {platformLabel}
              </span>
              <a
                href={evidence.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-semibold text-brand-600 hover:text-brand-700 hover:underline flex items-center gap-1 mt-0.5 break-all"
              >
                <span>{evidence.url}</span>
                <ExternalLink className="w-3.5 h-3.5 shrink-0 inline" />
              </a>
              <p className="text-xs text-slate-500 mt-1">
                Tautan publik telah diverifikasi dapat diakses oleh validator sekolah.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // File evidence preview
  const isPdf = evidence.mimeType === 'application/pdf' || evidence.fileName?.endsWith('.pdf');
  const isVideo = evidence.mimeType?.startsWith('video/') || evidence.fileName?.endsWith('.mp4');
  const isImage = evidence.mimeType?.startsWith('image/') || /\.(png|jpg|jpeg|webp)$/i.test(evidence.fileName || '');

  const FileIcon = isPdf ? FileText : isVideo ? Video : isImage ? ImageIcon : FileText;

  return (
    <div
      className={cn(
        'rounded-xl border border-slate-200 bg-white p-4 shadow-2xs hover:border-slate-300 transition-all',
        className
      )}
    >
      <div className="flex items-center gap-3.5">
        <div
          className={cn(
            'w-11 h-11 rounded-lg flex items-center justify-center shrink-0 border',
            isPdf && 'bg-red-50 text-red-600 border-red-200',
            isVideo && 'bg-purple-50 text-purple-600 border-purple-200',
            isImage && 'bg-blue-50 text-blue-600 border-blue-200'
          )}
        >
          <FileIcon className="w-5 h-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-slate-900 truncate">
            {evidence.fileName || 'Dokumen Bukti Karya'}
          </p>
          <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
            <span>{evidence.fileSize || 'Ukuran file ~2.4 MB'}</span>
            <span>•</span>
            <span className="uppercase">{isPdf ? 'PDF Document' : isVideo ? 'MP4 Video' : 'Image'}</span>
          </div>
        </div>
        <button
          type="button"
          onClick={() => alert(`Pratinjau mock untuk ${evidence.fileName || 'berkas'}`)}
          className="px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-medium transition-colors"
        >
          Buka Berkas
        </button>
      </div>

      {isImage && (
        <div className="mt-3 rounded-lg overflow-hidden border border-slate-200 bg-slate-100 p-2 text-center">
          <div className="h-32 rounded bg-slate-200/80 flex items-center justify-center text-slate-500 text-xs">
            [Pratinjau Gambar Purwarupa Desain / Dokumentasi]
          </div>
        </div>
      )}
    </div>
  );
};
