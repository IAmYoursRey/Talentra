import React, { useState, useRef } from 'react';
import { UploadCloud, File, CheckCircle2, AlertCircle, X, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';
import { EvidenceSource } from '../../types/portfolio.types';

interface MockFileUploaderProps {
  onFileSelect: (evidence: EvidenceSource | null) => void;
  selectedEvidence: EvidenceSource | null;
  className?: string;
  portfolioId?: string;
}

const ALLOWED_MIME_TYPES: Record<string, number> = {
  'application/pdf': 15 * 1024 * 1024, // 15MB
  'image/jpeg': 5 * 1024 * 1024,      // 5MB
  'image/png': 5 * 1024 * 1024,       // 5MB
  'video/mp4': 50 * 1024 * 1024,      // 50MB
};

export const MockFileUploader: React.FC<MockFileUploaderProps> = ({
  onFileSelect,
  selectedEvidence,
  className,
}) => {
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'validating' | 'ready' | 'error'>('idle');
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatSize = (bytes: number): string => {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleRealFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setErrorMessage('');
    // Client-side convenience validation
    const maxAllowed = ALLOWED_MIME_TYPES[file.type];
    if (!maxAllowed) {
      setUploadState('error');
      setErrorMessage('Format file tidak didukung. Harap unggah PDF, PNG, JPG, atau MP4.');
      return;
    }
    if (file.size > maxAllowed) {
      setUploadState('error');
      setErrorMessage(`Ukuran file melebihi batas (${(maxAllowed / (1024 * 1024)).toFixed(0)} MB untuk tipe ini).`);
      return;
    }

    startUploadPipeline(file.name, file.type, formatSize(file.size));
  };

  const startUploadPipeline = (fileName: string, mimeType: string, fileSize: string) => {
    setUploadState('uploading');
    setProgress(20);
    setErrorMessage('');

    // Simulate direct binary upload progression
    const uploadInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 85) {
          clearInterval(uploadInterval);
          // Step 2: Validating binary signature & magic bytes
          setUploadState('validating');
          setTimeout(() => {
            setUploadState('ready');
            onFileSelect({
              type: 'file',
              url: `/uploads/${fileName}`,
              fileName,
              fileSize,
              mimeType,
            });
          }, 800);
          return 95;
        }
        return prev + 25;
      });
    }, 150);
  };

  const handleSelectMockPreset = (preset: { name: string; type: string; size: string }) => {
    startUploadPipeline(preset.name, preset.type, preset.size);
  };

  const handleClear = () => {
    setUploadState('idle');
    setProgress(0);
    setErrorMessage('');
    onFileSelect(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center justify-between">
        <label className="block text-sm font-semibold text-slate-800">
          Unggah Berkas Bukti Karya
        </label>
        <span className="text-[11px] text-slate-500 font-medium">
          Maks. PDF 15MB • Gambar 5MB • MP4 50MB
        </span>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,.mp4"
        onChange={handleRealFileSelect}
        className="hidden"
      />

      {uploadState === 'idle' && !selectedEvidence && (
        <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-brand-400 bg-slate-50/50 transition-colors">
          <div className="w-12 h-12 mx-auto rounded-full bg-brand-50 text-brand-600 flex items-center justify-center mb-3">
            <UploadCloud className="w-6 h-6" />
          </div>
          <p className="text-sm font-medium text-slate-700">
            Tarik & lepaskan dokumen karya atau telusuri berkas
          </p>
          <p className="text-xs text-slate-500 mt-1 mb-4">
            Format resmi: <strong>PDF</strong>, <strong>JPG/PNG</strong>, <strong>MP4</strong>
          </p>

          <div className="flex flex-wrap items-center justify-center gap-2 mb-3">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="text-xs px-5 py-2.5 rounded-xl tal-btn-primary font-bold shadow-md"
            >
              Pilih Berkas dari Perangkat
            </button>
          </div>

          <div className="pt-3 border-t border-slate-200/80">
            <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider mb-2">
              Atau Gunakan Presisi Uji Sampel
            </p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              <button
                type="button"
                onClick={() => handleSelectMockPreset({ name: 'Dokumen_Portofolio_Karya.pdf', type: 'application/pdf', size: '2.4 MB' })}
                className="text-xs px-3.5 py-1.5 rounded-xl tal-btn-secondary font-semibold"
              >
                + Sampel PDF
              </button>
              <button
                type="button"
                onClick={() => handleSelectMockPreset({ name: 'Tangkapan_Layar_Sistem.png', type: 'image/png', size: '1.1 MB' })}
                className="text-xs px-3.5 py-1.5 rounded-xl tal-btn-secondary font-semibold"
              >
                + Sampel PNG
              </button>
              <button
                type="button"
                onClick={() => handleSelectMockPreset({ name: 'Video_Presentasi_Demo.mp4', type: 'video/mp4', size: '14.2 MB' })}
                className="text-xs px-3.5 py-1.5 rounded-xl tal-btn-secondary font-semibold"
              >
                + Sampel MP4
              </button>
            </div>
          </div>
        </div>
      )}

      {uploadState === 'uploading' && (
        <div className="border border-slate-200 rounded-xl p-5 bg-white space-y-2">
          <div className="flex items-center justify-between text-xs font-medium text-slate-700">
            <span className="flex items-center gap-1.5">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-600" />
              Mengunggah berkas biner secara privat...
            </span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
            <div
              className="bg-brand-500 h-2 rounded-full transition-all duration-200"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {uploadState === 'validating' && (
        <div className="border border-brand-200 bg-brand-50/50 rounded-xl p-4 flex items-center gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-brand-600 shrink-0" />
          <div>
            <p className="text-xs font-semibold text-brand-900">
              Memvalidasi Biner & Keamanan Berkas...
            </p>
            <p className="text-[11px] text-brand-700">
              Memeriksa magic-byte signature dan kesesuaian format terhadap kebijakan privasi.
            </p>
          </div>
        </div>
      )}

      {uploadState === 'error' && (
        <div className="border border-reject-300 bg-reject-50 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="w-5 h-5 text-reject-600 shrink-0" />
            <p className="text-xs font-semibold text-reject-800">
              {errorMessage || 'Validasi unggahan gagal. Format tidak sesuai.'}
            </p>
          </div>
          <button
            type="button"
            onClick={handleClear}
            className="text-xs text-reject-700 hover:text-reject-900 font-semibold underline ml-2"
          >
            Coba Lagi
          </button>
        </div>
      )}

      {(uploadState === 'ready' || (selectedEvidence && selectedEvidence.type === 'file')) && (
        <div className="border border-endorse-300 bg-endorse-50/40 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-endorse-100 text-endorse-700 flex items-center justify-center shrink-0">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">
                {selectedEvidence?.fileName || 'Berkas Terunggah'}
              </p>
              <p className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                <span>{selectedEvidence?.fileSize || 'Tervalidasi'}</span>
                <span>•</span>
                <span className="text-endorse-700 font-semibold">Tervalidasi & Siap Diajukan</span>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleClear}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-white transition-colors"
            aria-label="Hapus berkas"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
