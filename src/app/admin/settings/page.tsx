'use client';

import React, { useState } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { ShieldCheck, School, Database, FileCheck2, Check, Lock, Sliders } from 'lucide-react';

export default function AdminSettingsPage() {
  const [schoolName, setSchoolName] = useState('SMAN 1 Ngoro');
  const [academicYear, setAcademicYear] = useState('2026 / 2027');
  const [demoLogin, setDemoLogin] = useState(false);
  const [secureCookie] = useState('ON');
  const [rbacMode] = useState('STRICT');
  const [freeTier] = useState('ON');
  const [privateFiles] = useState('ON');
  const [softLimit] = useState('Configured');
  const [evidenceMax, setEvidenceMax] = useState(8);
  const [qrVerification] = useState('ON');
  const [revocationMode] = useState('Immediate');

  const [savedMsg, setSavedMsg] = useState('');

  const handleSave = (section: string) => {
    setSavedMsg(`Pengaturan ${section} berhasil diperbarui.`);
    setTimeout(() => setSavedMsg(''), 3000);
  };

  return (
    <AppShell pageTitle="School Settings" expectedRole="admin">
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header matching 21-Admin-Settings-HF.svg */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#261331] tracking-tight">
              School Settings
            </h1>
            <p className="text-sm text-[#6F607D] mt-1">
              Konfigurasi institusi, keamanan, storage, dan kebijakan CV.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#F3E8FF] border border-purple-200 text-[#6D28D9] font-bold text-xs shadow-xs self-start sm:self-auto">
            <span>2026 • Semester 1</span>
          </div>
        </div>

        {savedMsg && (
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold flex items-center gap-2 animate-in fade-in">
            <Check className="w-4 h-4 text-emerald-600" />
            <span>{savedMsg}</span>
          </div>
        )}

        {/* 4 Settings Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card 1: Identitas Sekolah */}
          <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 sm:p-7 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between">
            <div className="space-y-5">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-purple-100 text-[#6D28D9] flex items-center justify-center">
                  <School className="w-4 h-4" />
                </div>
                <h2 className="text-base font-extrabold text-[#261331]">Identitas Sekolah</h2>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Nama sekolah</span>
                  <span className="font-bold text-[#261331]">{schoolName}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Tahun akademik</span>
                  <span className="font-bold text-[#261331]">{academicYear}</span>
                </div>
              </div>
            </div>

            <div className="pt-6">
              <button
                type="button"
                onClick={() => handleSave('Identitas Sekolah')}
                className="px-6 py-2.5 rounded-xl tal-btn-primary font-bold text-xs shadow-md"
              >
                Edit data
              </button>
            </div>
          </div>

          {/* Card 2: Keamanan */}
          <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 sm:p-7 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between">
            <div className="space-y-5">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-purple-100 text-[#6D28D9] flex items-center justify-center">
                  <Lock className="w-4 h-4" />
                </div>
                <h2 className="text-base font-extrabold text-[#261331]">Keamanan</h2>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Demo login</span>
                  <span className="font-bold text-[#261331]">{demoLogin ? 'ON' : 'OFF'}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Secure cookie</span>
                  <span className="font-bold text-[#261331]">{secureCookie}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">RBAC</span>
                  <span className="font-bold text-[#261331]">{rbacMode}</span>
                </div>
              </div>
            </div>

            <div className="pt-6">
              <button
                type="button"
                onClick={() => {
                  setDemoLogin(!demoLogin);
                  handleSave('Keamanan');
                }}
                className="px-6 py-2.5 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs shadow-md transition-colors"
              >
                Security policy
              </button>
            </div>
          </div>

          {/* Card 3: Storage & Upload */}
          <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 sm:p-7 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between">
            <div className="space-y-5">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-purple-100 text-[#6D28D9] flex items-center justify-center">
                  <Database className="w-4 h-4" />
                </div>
                <h2 className="text-base font-extrabold text-[#261331]">Storage & Upload</h2>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Free-tier mode</span>
                  <span className="font-bold text-[#261331]">{freeTier}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Private files</span>
                  <span className="font-bold text-[#261331]">{privateFiles}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Soft limit</span>
                  <span className="font-bold text-[#261331]">{softLimit}</span>
                </div>
              </div>
            </div>

            <div className="pt-6">
              <button
                type="button"
                onClick={() => handleSave('Storage & Kuota')}
                className="px-6 py-2.5 rounded-xl tal-btn-primary font-bold text-xs shadow-md"
              >
                Atur kuota
              </button>
            </div>
          </div>

          {/* Card 4: CV & Verification */}
          <div className="bg-white rounded-[18px] border border-[#E9E1F4] p-6 sm:p-7 shadow-[0_4px_16px_rgba(76,29,149,0.06)] flex flex-col justify-between">
            <div className="space-y-5">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-purple-100 text-[#6D28D9] flex items-center justify-center">
                  <FileCheck2 className="w-4 h-4" />
                </div>
                <h2 className="text-base font-extrabold text-[#261331]">CV & Verification</h2>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Evidence max</span>
                  <span className="font-bold text-[#261331]">{evidenceMax}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">QR verification</span>
                  <span className="font-bold text-[#261331]">{qrVerification}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[#E9E1F4]">
                  <span className="font-semibold text-[#6F607D]">Revocation</span>
                  <span className="font-bold text-[#261331]">{revocationMode}</span>
                </div>
              </div>
            </div>

            <div className="pt-6">
              <button
                type="button"
                onClick={() => handleSave('Kebijakan CV')}
                className="px-6 py-2.5 rounded-xl bg-[#8B5CF6] hover:bg-purple-600 text-white font-bold text-xs shadow-md transition-colors"
              >
                Atur kebijakan
              </button>
            </div>
          </div>
        </div>

        {/* Footer info notice */}
        <p className="text-[11px] text-[#6F607D] font-medium pt-2">
          Semua perubahan settings bersifat institusional dan hanya dapat diakses admin sekolah.
        </p>
      </div>
    </AppShell>
  );
}
