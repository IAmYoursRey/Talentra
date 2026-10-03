'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';
import { EmptyState } from '../../../components/common/EmptyState';
import { ErrorState } from '../../../components/common/ErrorState';
import { ConfirmDialog } from '../../../components/common/ConfirmDialog';
import { adminClassService } from '../../../services/admin-class.service';
import { adminUserService } from '../../../services/admin-user.service';
import {
  AdminClass,
  AdminClassDetail,
  CreateClassPayload,
  UpdateClassPayload,
  AdminUser,
} from '../../../types/admin.types';
import {
  School,
  Users,
  ShieldCheck,
  Plus,
  ChevronRight,
  UserCheck,
  CheckCircle2,
  AlertCircle,
  X,
  Archive,
  UserMinus,
  UserPlus,
  Shield,
  Edit2,
} from 'lucide-react';
import { useOffline } from '../../../context/OfflineContext';

export default function AdminClassesPage() {
  const [classes, setClasses] = useState<AdminClass[]>(() => adminClassService.getCachedClasses({ status: 'active' }));
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const { isOffline } = useOffline();

  // Filters
  const [search, setSearch] = useState('');
  const [gradeFilter, setGradeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('active');

  // Class detail drawer
  const [selectedClassId, setSelectedClassId] = useState<string | null>(null);
  const [classDetail, setClassDetail] = useState<AdminClassDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [activeTab, setActiveTab] = useState<'students' | 'teachers'>('teachers');

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isAssignTeacherOpen, setIsAssignTeacherOpen] = useState(false);
  const [isEnrollStudentOpen, setIsEnrollStudentOpen] = useState(false);

  // Pool data for assigning
  const [availableTeachers, setAvailableTeachers] = useState<AdminUser[]>([]);
  const [availableStudents, setAvailableStudents] = useState<AdminUser[]>([]);
  const [selectedTeacherId, setSelectedTeacherId] = useState('');
  const [selectedStudentId, setSelectedStudentId] = useState('');

  // Confirmation state
  const [confirmArchiveId, setConfirmArchiveId] = useState<string | null>(null);
  const [confirmRemoveTeacherId, setConfirmRemoveTeacherId] = useState<string | null>(null);
  const [confirmUnenrollStudentId, setConfirmUnenrollStudentId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackBanner, setFeedbackBanner] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Form states
  const [classForm, setClassForm] = useState<CreateClassPayload>({
    name: '',
    gradeLevel: '10',
    academicYear: '2025/2026',
  });

  const loadClasses = useCallback(async () => {
    setErrorMsg(null);
    try {
      const data = await adminClassService.listClasses({
        gradeLevel: gradeFilter !== 'all' ? gradeFilter : undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        search: search.trim() || undefined,
      });
      setClasses(data);
    } catch (err: unknown) {
      if (typeof window !== 'undefined' && !window.navigator.onLine) {
        setClasses(adminClassService.getCachedClasses({
          gradeLevel: gradeFilter !== 'all' ? gradeFilter : undefined,
          status: statusFilter !== 'all' ? statusFilter : undefined,
          search: search.trim() || undefined,
        }));
      }
    }
  }, [gradeFilter, statusFilter, search]);

  useEffect(() => {
    loadClasses();
  }, [loadClasses]);

  const loadDetail = useCallback(async (classId: string) => {
    setIsLoadingDetail(true);
    try {
      const detail = await adminClassService.getClass(classId);
      setClassDetail(detail);
    } catch {
      // fallback
    } finally {
      setIsLoadingDetail(false);
    }
  }, []);

  const handleSelectClass = async (cls: AdminClass) => {
    setSelectedClassId(cls.id);
    const cached = adminClassService.getCachedClassDetail(cls.id);
    if (cached) {
      setClassDetail(cached);
    }
    await loadDetail(cls.id);
  };

  const showFeedback = (type: 'success' | 'error', message: string) => {
    setFeedbackBanner({ type, message });
    setTimeout(() => setFeedbackBanner(null), 5000);
  };

  // Create class
  const handleCreateClass = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!classForm.name.trim()) return;
    setIsSubmitting(true);
    try {
      await adminClassService.createClass(classForm);
      setIsCreateModalOpen(false);
      setClassForm({ name: '', gradeLevel: '10', academicYear: '2025/2026' });
      showFeedback('success', `Rombel ${classForm.name} berhasil dibuat.`);
      await loadClasses();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal membuat rombel.';
      showFeedback('error', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Archive class
  const handleArchiveClass = async () => {
    if (!confirmArchiveId) return;
    setIsSubmitting(true);
    try {
      await adminClassService.archiveClass(confirmArchiveId);
      showFeedback('success', 'Rombongan belajar berhasil diarsipkan.');
      setConfirmArchiveId(null);
      if (selectedClassId === confirmArchiveId) {
        setSelectedClassId(null);
        setClassDetail(null);
      }
      await loadClasses();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal mengarsipkan rombel.';
      showFeedback('error', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Open Teacher Assignment Modal
  const handleOpenAssignTeacher = async () => {
    try {
      const res = await adminUserService.listUsers({ role: 'teacher', status: 'active' });
      setAvailableTeachers(res.items);
      setSelectedTeacherId(res.items[0]?.id || '');
      setIsAssignTeacherOpen(true);
    } catch {
      showFeedback('error', 'Gagal memuat daftar guru aktif.');
    }
  };

  // Assign Teacher
  const handleAssignTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClassId || !selectedTeacherId) return;
    setIsSubmitting(true);
    try {
      await adminClassService.assignTeacher(selectedClassId, selectedTeacherId, 'validator');
      setIsAssignTeacherOpen(false);
      showFeedback('success', 'Guru validator berhasil ditugaskan ke rombel.');
      await loadDetail(selectedClassId);
      await loadClasses();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal menugaskan guru.';
      showFeedback('error', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Remove Teacher Assignment
  const handleRemoveTeacher = async () => {
    if (!selectedClassId || !confirmRemoveTeacherId) return;
    setIsSubmitting(true);
    try {
      await adminClassService.removeTeacherAssignment(selectedClassId, confirmRemoveTeacherId);
      setConfirmRemoveTeacherId(null);
      showFeedback('success', 'Penugasan guru validator berhasil dicabut.');
      await loadDetail(selectedClassId);
      await loadClasses();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal mencabut penugasan guru.';
      showFeedback('error', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Open Student Enrollment Modal
  const handleOpenEnrollStudent = async () => {
    try {
      const res = await adminUserService.listUsers({ role: 'student', status: 'active' });
      setAvailableStudents(res.items);
      setSelectedStudentId(res.items[0]?.id || '');
      setIsEnrollStudentOpen(true);
    } catch {
      showFeedback('error', 'Gagal memuat daftar siswa aktif.');
    }
  };

  // Enroll Student
  const handleEnrollStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClassId || !selectedStudentId) return;
    setIsSubmitting(true);
    try {
      await adminClassService.enrollStudent(selectedClassId, selectedStudentId);
      setIsEnrollStudentOpen(false);
      showFeedback('success', 'Siswa berhasil didaftarkan ke rombel.');
      await loadDetail(selectedClassId);
      await loadClasses();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal mendaftarkan siswa.';
      showFeedback('error', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Unenroll Student
  const handleUnenrollStudent = async () => {
    if (!selectedClassId || !confirmUnenrollStudentId) return;
    setIsSubmitting(true);
    try {
      await adminClassService.unenrollStudent(selectedClassId, confirmUnenrollStudentId);
      setConfirmUnenrollStudentId(null);
      showFeedback('success', 'Siswa berhasil dinonaktifkan dari rombel.');
      await loadDetail(selectedClassId);
      await loadClasses();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal mengeluarkan siswa.';
      showFeedback('error', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppShell pageTitle="Class Management" expectedRole="admin" isPageLoading={isLoading}>
      <div className="space-y-6">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-xl sm:text-2xl font-black text-[#261331] tracking-tight">
                Class Management
              </h2>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#F7F2FF] text-[#6D28D9] border border-[#E9E1F4]">
                2026 • Semester 1
              </span>
            </div>
            <p className="text-xs sm:text-sm text-[#6F607D]">
              Atur rombongan belajar dan assignment validator.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl tal-btn-primary font-semibold text-xs self-start sm:self-center"
          >
            <Plus className="w-4 h-4" />
            <span>Tambah Kelas</span>
          </button>
        </div>

        {/* Feedback Banner */}
        {feedbackBanner && (
          <div
            className={`p-4 rounded-xl border text-xs flex items-center justify-between transition-all ${
              feedbackBanner.type === 'success'
                ? 'bg-endorse-50 border-endorse-300 text-endorse-800'
                : 'bg-reject-50 border-reject-300 text-reject-800'
            }`}
          >
            <div className="flex items-center gap-2">
              {feedbackBanner.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-endorse-600 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-reject-600 shrink-0" />
              )}
              <p className="font-semibold">{feedbackBanner.message}</p>
            </div>
            <button
              type="button"
              onClick={() => setFeedbackBanner(null)}
              className="p-1 hover:opacity-75 font-bold"
              aria-label="Tutup notifikasi"
            >
              ✕
            </button>
          </div>
        )}

        {/* Filter Controls */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-[#E9E1F4] shadow-tal-card">
          <div className="flex items-center gap-2 flex-1">
            <select
              value={gradeFilter}
              onChange={(e) => setGradeFilter(e.target.value)}
              className="px-3 py-2 bg-[#F7F2FF] border border-[#E9E1F4] rounded-xl text-xs sm:text-sm text-[#261331] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
            >
              <option value="all">Semua Tingkat</option>
              <option value="10">Kelas 10</option>
              <option value="11">Kelas 11</option>
              <option value="12">Kelas 12</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-[#F7F2FF] border border-[#E9E1F4] rounded-xl text-xs sm:text-sm text-[#261331] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
            >
              <option value="all">Semua Status</option>
              <option value="active">Rombel Aktif</option>
              <option value="archived">Diarsipkan</option>
            </select>
          </div>

          <div className="text-xs text-[#6F607D]">
            Total <strong>{classes.length}</strong> rombel ditemukan
          </div>
        </div>

        {/* Classes Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="bg-white p-6 rounded-2xl border border-[#E9E1F4]">
                <LoadingSkeleton rows={4} />
              </div>
            ))}
          </div>
        ) : errorMsg ? (
          <ErrorState message={errorMsg} onRetry={loadClasses} />
        ) : classes.length === 0 ? (
          <EmptyState
            title="Tidak Ada Rombel Ditemukan"
            description="Belum ada rombongan belajar yang terdaftar sesuai filter yang dipilih."
            actionLabel="Tambah Rombel"
            onAction={() => setIsCreateModalOpen(true)}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {classes.map((cls, idx) => (
              <div
                key={cls.id}
                className="bg-white rounded-2xl border border-[#E9E1F4] p-5 shadow-tal-card tal-card-hover transition-all flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="w-7 h-7 rounded-full bg-[#F7F2FF] border border-[#E9E1F4] text-[#6D28D9] text-xs font-bold flex items-center justify-center">
                      {idx + 1}
                    </span>
                    <span className="text-[11px] font-bold text-[#6D28D9] bg-[#F7F2FF] px-2 py-0.5 rounded-md border border-[#E9E1F4]">
                      Tingkat {cls.gradeLevel}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-lg font-black text-[#261331]">{cls.name}</h3>
                    <p className="text-xs text-[#6F607D] font-medium mt-0.5">
                      {cls.studentsCount} siswa
                    </p>
                    <p className="text-xs text-[#4C1D95] font-semibold mt-1 flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-[#8B5CF6]" />
                      <span>Validator: {cls.validatorsCount > 0 ? `${cls.validatorsCount} Guru Ditugaskan` : 'Belum Ditugaskan'}</span>
                    </p>
                  </div>
                </div>

                <div className="pt-3 border-t border-[#E9E1F4] flex items-center justify-between">
                  {cls.status === 'active' ? (
                    <button
                      type="button"
                      onClick={() => setConfirmArchiveId(cls.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                      title="Arsipkan Rombel"
                      aria-label={`Arsipkan ${cls.name}`}
                    >
                      <Archive className="w-4 h-4" />
                    </button>
                  ) : (
                    <span className="text-[11px] text-slate-400">Arsip</span>
                  )}

                  <button
                    type="button"
                    onClick={() => handleSelectClass(cls)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl tal-btn-secondary font-semibold text-xs"
                  >
                    <span>Kelola</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Assignment Policy Info Footer */}
        <div className="bg-[#F7F2FF] rounded-2xl border border-[#E9E1F4] p-4 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-white border border-[#E9E1F4] text-[#6D28D9] flex items-center justify-center shrink-0 shadow-2xs">
            <Shield className="w-4.5 h-4.5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-[#261331]">Aturan assignment</h4>
            <p className="text-[11px] text-[#6F607D]">
              Guru hanya dapat melihat dan memvalidasi kelas yang ditugaskan.
            </p>
          </div>
        </div>

        {/* Class Detail Drawer Modal */}
        {selectedClassId && classDetail && (
          <div
            className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-end"
            onClick={() => {
              setSelectedClassId(null);
              setClassDetail(null);
            }}
          >
            <div
              className="w-full max-w-lg bg-white h-full shadow-2xl p-6 sm:p-8 flex flex-col justify-between overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="space-y-6">
                <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                  <div className="flex items-center gap-2">
                    <div className="w-9 h-9 rounded-xl bg-intelligence-50 text-intelligence-600 flex items-center justify-center font-bold">
                      <School className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">{classDetail.name}</h3>
                      <p className="text-xs text-slate-500">Tingkat {classDetail.gradeLevel} • T.A. {classDetail.academicYear}</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedClassId(null);
                      setClassDetail(null);
                    }}
                    aria-label="Tutup panel"
                    className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Tab switch */}
                <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
                  <button
                    type="button"
                    onClick={() => setActiveTab('teachers')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      activeTab === 'teachers'
                        ? 'bg-growth-50 text-growth-700 border border-growth-200'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    Guru Ditugaskan ({classDetail.teachers.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('students')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      activeTab === 'students'
                        ? 'bg-brand-50 text-brand-700 border border-brand-200'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    Siswa Terdaftar ({classDetail.students.length})
                  </button>
                </div>

                {/* Tab Content: Teachers */}
                {activeTab === 'teachers' && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-slate-500">
                        Penugasan mengontrol akses antrean validasi guru pada rombel ini.
                      </p>
                      <button
                        type="button"
                        onClick={handleOpenAssignTeacher}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-growth-600 hover:bg-growth-700 text-white font-semibold text-xs shadow-2xs"
                      >
                        <UserPlus className="w-3.5 h-3.5" />
                        <span>Tugaskan Guru</span>
                      </button>
                    </div>

                    {classDetail.teachers.length === 0 ? (
                      <div className="p-4 bg-slate-50 rounded-xl text-center text-xs text-slate-500">
                        Belum ada guru validator yang ditugaskan ke rombel ini.
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {classDetail.teachers.map((t) => (
                          <div
                            key={t.id}
                            className="p-3 bg-white border border-slate-200 rounded-xl flex items-center justify-between hover:border-slate-300 transition-colors shadow-2xs"
                          >
                            <div className="flex items-center gap-2.5">
                              <ShieldCheck className="w-4 h-4 text-growth-600 shrink-0" />
                              <div>
                                <p className="text-xs font-bold text-slate-900">{t.displayName}</p>
                                <p className="text-[11px] text-slate-400">{t.title || 'Guru Validator'}</p>
                              </div>
                            </div>

                            <button
                              type="button"
                              onClick={() => setConfirmRemoveTeacherId(t.id)}
                              className="p-1.5 rounded-lg text-slate-400 hover:text-reject-600 hover:bg-reject-50 transition-colors"
                              title="Cabut Penugasan"
                            >
                              <UserMinus className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Tab Content: Students */}
                {activeTab === 'students' && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-slate-500">
                        Siswa aktif yang terdaftar dalam rombongan belajar ini.
                      </p>
                      <button
                        type="button"
                        onClick={handleOpenEnrollStudent}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs shadow-2xs"
                      >
                        <UserPlus className="w-3.5 h-3.5" />
                        <span>Daftarkan Siswa</span>
                      </button>
                    </div>

                    {classDetail.students.length === 0 ? (
                      <div className="p-4 bg-slate-50 rounded-xl text-center text-xs text-slate-500">
                        Belum ada siswa yang didaftarkan ke rombel ini.
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                        {classDetail.students.map((s) => (
                          <div
                            key={s.id}
                            className="p-3 bg-white border border-slate-200 rounded-xl flex items-center justify-between hover:border-slate-300 transition-colors shadow-2xs"
                          >
                            <div>
                              <p className="text-xs font-bold text-slate-900">{s.displayName}</p>
                              <p className="text-[11px] font-mono text-slate-400">{s.maskedIdentifier}</p>
                            </div>

                            <button
                              type="button"
                              onClick={() => setConfirmUnenrollStudentId(s.id)}
                              className="p-1.5 rounded-lg text-slate-400 hover:text-reject-600 hover:bg-reject-50 transition-colors"
                              title="Keluarkan dari Rombel"
                            >
                              <UserMinus className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="pt-6 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedClassId(null);
                    setClassDetail(null);
                  }}
                  className="w-full py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-colors"
                >
                  Tutup Panel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Create Class */}
        {isCreateModalOpen && (
          <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Tambah Rombel Baru</h3>
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleCreateClass} className="space-y-3.5 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Nama Rombongan Belajar</label>
                  <input
                    type="text"
                    required
                    value={classForm.name}
                    onChange={(e) => setClassForm({ ...classForm, name: e.target.value })}
                    placeholder="Contoh: XII RPL 1"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Tingkat Kelas</label>
                    <select
                      value={classForm.gradeLevel}
                      onChange={(e) => setClassForm({ ...classForm, gradeLevel: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
                    >
                      <option value="10">Kelas 10</option>
                      <option value="11">Kelas 11</option>
                      <option value="12">Kelas 12</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Tahun Ajaran</label>
                    <input
                      type="text"
                      required
                      value={classForm.academicYear}
                      onChange={(e) => setClassForm({ ...classForm, academicYear: e.target.value })}
                      placeholder="2025/2026"
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
                    />
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setIsCreateModalOpen(false)}
                    className="px-3.5 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold text-xs hover:bg-slate-50"
                  >
                    Batal
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded-xl bg-intelligence-600 hover:bg-intelligence-700 text-white font-semibold text-xs transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? 'Menyimpan...' : 'Simpan Rombel'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Assign Teacher */}
        {isAssignTeacherOpen && (
          <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Tugaskan Guru Validator</h3>
                <button
                  type="button"
                  onClick={() => setIsAssignTeacherOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleAssignTeacher} className="space-y-3.5 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Pilih Guru Pendidik</label>
                  <select
                    value={selectedTeacherId}
                    onChange={(e) => setSelectedTeacherId(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-growth-500"
                  >
                    {availableTeachers.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.displayName} ({t.maskedIdentifier})
                      </option>
                    ))}
                  </select>
                  <p className="text-[10px] text-slate-400 mt-1">
                    Guru yang ditugaskan akan mendapatkan otoritas validasi pada portofolio siswa rombel ini.
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setIsAssignTeacherOpen(false)}
                    className="px-3.5 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold text-xs hover:bg-slate-50"
                  >
                    Batal
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || !selectedTeacherId}
                    className="px-4 py-2 rounded-xl bg-growth-600 hover:bg-growth-700 text-white font-semibold text-xs transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? 'Menugaskan...' : 'Tugaskan Guru'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Enroll Student */}
        {isEnrollStudentOpen && (
          <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Daftarkan Siswa ke Rombel</h3>
                <button
                  type="button"
                  onClick={() => setIsEnrollStudentOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleEnrollStudent} className="space-y-3.5 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Pilih Siswa</label>
                  <select
                    value={selectedStudentId}
                    onChange={(e) => setSelectedStudentId(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    {availableStudents.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.displayName} ({s.maskedIdentifier})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setIsEnrollStudentOpen(false)}
                    className="px-3.5 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold text-xs hover:bg-slate-50"
                  >
                    Batal
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || !selectedStudentId}
                    className="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? 'Mendaftarkan...' : 'Daftarkan Siswa'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Confirm Archive */}
        <ConfirmDialog
          isOpen={!!confirmArchiveId}
          title="Konfirmasi Pengarsipan Rombel"
          description="Apakah Anda yakin ingin mengarsipkan rombongan belajar ini? Data riwayat pendaftaran dan validasi masa lalu akan tetap tersimpan secara permanen untuk kebutuhan audit dan transkrip."
          confirmLabel="Ya, Arsipkan"
          variant="warning"
          onConfirm={handleArchiveClass}
          onCancel={() => setConfirmArchiveId(null)}
        />

        {/* Confirm Remove Teacher Assignment */}
        <ConfirmDialog
          isOpen={!!confirmRemoveTeacherId}
          title="Konfirmasi Pencabutan Penugasan Guru"
          description="Pencabutan penugasan ini akan menghapus akses antrean validasi guru pada rombel ini ke depannya. Keputusan validasi masa lalu yang telah diselesaikan tetap teratribusi secara sah kepada guru ini."
          confirmLabel="Cabut Penugasan"
          variant="danger"
          onConfirm={handleRemoveTeacher}
          onCancel={() => setConfirmRemoveTeacherId(null)}
        />

        {/* Confirm Unenroll Student */}
        <ConfirmDialog
          isOpen={!!confirmUnenrollStudentId}
          title="Keluarkan Siswa dari Rombel"
          description="Siswa akan dinonaktifkan dari rombel ini untuk tahun ajaran aktif, namun riwayat portofolio dan capaian kompetensinya tetap terjaga utuh."
          confirmLabel="Keluarkan Siswa"
          variant="warning"
          onConfirm={handleUnenrollStudent}
          onCancel={() => setConfirmUnenrollStudentId(null)}
        />
      </div>
    </AppShell>
  );
}
