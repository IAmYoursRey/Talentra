'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { AppShell } from '../../../components/layout/AppShell';
import { ConfirmDialog } from '../../../components/common/ConfirmDialog';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';
import { EmptyState } from '../../../components/common/EmptyState';
import { ErrorState } from '../../../components/common/ErrorState';
import { adminUserService } from '../../../services/admin-user.service';
import { adminClassService } from '../../../services/admin-class.service';
import {
  AdminUser,
  CreateStudentPayload,
  CreateTeacherPayload,
  UpdateUserProfilePayload,
  UserCredentialResult,
  AdminClass,
} from '../../../types/admin.types';
import {
  Users,
  Search,
  Plus,
  KeyRound,
  UserX,
  UserCheck,
  CheckCircle2,
  AlertCircle,
  Shield,
  GraduationCap,
  Copy,
  Check,
  X,
  Edit,
  Lock,
} from 'lucide-react';

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [classes, setClasses] = useState<AdminClass[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [classFilter, setClassFilter] = useState<string>('all');

  // Modals state
  const [isStudentModalOpen, setIsStudentModalOpen] = useState(false);
  const [isTeacherModalOpen, setIsTeacherModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [credentialResult, setCredentialResult] = useState<UserCredentialResult | null>(null);
  const [copiedPassword, setCopiedPassword] = useState(false);

  // Confirmation state
  const [targetUser, setTargetUser] = useState<AdminUser | null>(null);
  const [confirmAction, setConfirmAction] = useState<'reset_password' | 'disable_account' | 'reactivate_account' | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackBanner, setFeedbackBanner] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Form states
  const [studentForm, setStudentForm] = useState<CreateStudentPayload>({
    displayName: '',
    nisn: '',
    gradeLevel: '10',
    classId: '',
  });

  const [teacherForm, setTeacherForm] = useState<CreateTeacherPayload>({
    displayName: '',
    identifier: '',
    title: '',
  });

  const [editForm, setEditForm] = useState<UpdateUserProfilePayload>({
    displayName: '',
    gradeLevel: '10',
    title: '',
  });

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const [userRes, classList] = await Promise.all([
        adminUserService.listUsers({
          role: roleFilter !== 'all' ? roleFilter : undefined,
          status: statusFilter !== 'all' ? statusFilter : undefined,
          classId: classFilter !== 'all' ? classFilter : undefined,
          search: search.trim() || undefined,
        }),
        adminClassService.listClasses({ status: 'active' }),
      ]);
      setUsers(userRes.items);
      setClasses(classList);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal memuat data pengguna dari server.';
      setErrorMsg(msg);
    } finally {
      setIsLoading(false);
    }
  }, [roleFilter, statusFilter, classFilter, search]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const showFeedback = (type: 'success' | 'error', message: string) => {
    setFeedbackBanner({ type, message });
    setTimeout(() => setFeedbackBanner(null), 5000);
  };

  // Handlers for creating student
  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentForm.displayName.trim() || !studentForm.nisn.trim()) {
      showFeedback('error', 'Nama lengkap dan NISN wajib diisi.');
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await adminUserService.createStudent(studentForm);
      setIsStudentModalOpen(false);
      setStudentForm({ displayName: '', nisn: '', gradeLevel: '10', classId: '' });
      setCredentialResult(res);
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal membuat akun siswa.';
      showFeedback('error', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handlers for creating teacher
  const handleCreateTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!teacherForm.displayName.trim() || !teacherForm.identifier.trim()) {
      showFeedback('error', 'Nama lengkap dan NUPTK/NIP wajib diisi.');
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await adminUserService.createTeacher(teacherForm);
      setIsTeacherModalOpen(false);
      setTeacherForm({ displayName: '', identifier: '', title: '' });
      setCredentialResult(res);
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal membuat akun pendidik.';
      showFeedback('error', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handlers for editing user
  const handleOpenEdit = (user: AdminUser) => {
    setEditingUser(user);
    setEditForm({
      displayName: user.displayName,
      gradeLevel: user.gradeLevel || '10',
      title: user.title || '',
    });
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    setIsSubmitting(true);
    try {
      await adminUserService.updateUser(editingUser.id, editForm);
      setEditingUser(null);
      showFeedback('success', `Profil ${editingUser.displayName} berhasil diperbarui.`);
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal memperbarui profil pengguna.';
      showFeedback('error', msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Confirmation dialog execute
  const handleExecuteAction = async () => {
    if (!targetUser || !confirmAction) return;
    setIsSubmitting(true);
    try {
      if (confirmAction === 'reset_password') {
        const res = await adminUserService.resetPassword(targetUser.id);
        setCredentialResult({
          ...res,
          displayName: targetUser.displayName,
          maskedIdentifier: targetUser.maskedIdentifier,
          role: targetUser.role,
        });
        showFeedback('success', `Kata sandi ${targetUser.displayName} berhasil diatur ulang.`);
      } else if (confirmAction === 'disable_account') {
        await adminUserService.disableUser(targetUser.id);
        showFeedback('success', `Akun ${targetUser.displayName} berhasil dinonaktifkan.`);
      } else if (confirmAction === 'reactivate_account') {
        await adminUserService.reactivateUser(targetUser.id);
        showFeedback('success', `Akun ${targetUser.displayName} berhasil diaktifkan kembali.`);
      }
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Tindakan keamanan gagal diproses.';
      showFeedback('error', msg);
    } finally {
      setIsSubmitting(false);
      setTargetUser(null);
      setConfirmAction(null);
    }
  };

  const handleCopyPassword = () => {
    if (credentialResult?.temporaryPassword) {
      navigator.clipboard.writeText(credentialResult.temporaryPassword);
      setCopiedPassword(true);
      setTimeout(() => setCopiedPassword(false), 2500);
    }
  };

  return (
    <AppShell pageTitle="Manajemen Pengguna" expectedRole="admin">
      <div className="space-y-6">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
              Manajemen Akun Siswa & Validator
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
              Otoritas sekolah terverifikasi: kelola identitas terlindungi, status akun, dan kata sandi sementara.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={() => setIsTeacherModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors shadow-2xs"
            >
              <GraduationCap className="w-4 h-4 text-growth-600" />
              <span>Tambah Guru</span>
            </button>

            <button
              type="button"
              onClick={() => setIsStudentModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-intelligence-600 hover:bg-intelligence-700 text-white text-xs font-semibold transition-colors shadow-xs"
            >
              <Plus className="w-4 h-4" />
              <span>Tambah Siswa</span>
            </button>
          </div>
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

        {/* Filters Bar */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs space-y-3">
          <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Cari berdasarkan nama, email, atau identitas ter-mask..."
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500 transition-colors"
              />
            </div>

            {/* Class filter */}
            <div className="flex items-center gap-2">
              <select
                value={classFilter}
                onChange={(e) => setClassFilter(e.target.value)}
                className="px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
              >
                <option value="all">Semua Rombel</option>
                {classes.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.gradeLevel})
                  </option>
                ))}
              </select>

              {/* Status filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
              >
                <option value="all">Semua Status</option>
                <option value="active">Aktif</option>
                <option value="disabled">Dinonaktifkan</option>
              </select>
            </div>
          </div>

          {/* Role tabs */}
          <div className="flex items-center gap-2 pt-1 border-t border-slate-100 text-xs">
            <button
              type="button"
              onClick={() => setRoleFilter('all')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${
                roleFilter === 'all'
                  ? 'bg-slate-900 text-white shadow-2xs'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Semua Peran ({users.length})
            </button>
            <button
              type="button"
              onClick={() => setRoleFilter('student')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${
                roleFilter === 'student'
                  ? 'bg-brand-500 text-white shadow-2xs'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Siswa
            </button>
            <button
              type="button"
              onClick={() => setRoleFilter('teacher')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${
                roleFilter === 'teacher'
                  ? 'bg-growth-600 text-white shadow-2xs'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Guru Validator
            </button>
          </div>
        </div>

        {/* Data Display */}
        {isLoading ? (
          <div className="bg-white p-6 rounded-2xl border border-slate-200">
            <LoadingSkeleton rows={5} />
          </div>
        ) : errorMsg ? (
          <ErrorState message={errorMsg} onRetry={loadData} />
        ) : users.length === 0 ? (
          <EmptyState
            title="Tidak Ada Pengguna Ditemukan"
            description="Tidak ada data siswa atau guru yang cocok dengan kriteria pencarian dan filter saat ini."
            actionLabel="Reset Filter"
            onAction={() => {
              setSearch('');
              setRoleFilter('all');
              setStatusFilter('all');
              setClassFilter('all');
            }}
          />
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] font-semibold border-b border-slate-200">
                  <tr>
                    <th scope="col" className="px-5 py-3">Nama Pengguna</th>
                    <th scope="col" className="px-4 py-3">Peran</th>
                    <th scope="col" className="px-4 py-3">Identitas Ter-Mask</th>
                    <th scope="col" className="px-4 py-3">Rombel / Penugasan</th>
                    <th scope="col" className="px-4 py-3">Status</th>
                    <th scope="col" className="px-5 py-3 text-right">Tindakan Keamanan</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50/70 transition-colors">
                      {/* Name & Avatar */}
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs shrink-0 border border-slate-200">
                            {u.displayName.charAt(0)}
                          </div>
                          <div className="min-w-0">
                            <p className="font-bold text-slate-900 truncate">{u.displayName}</p>
                            <p className="text-[11px] text-slate-400 truncate">{u.email}</p>
                          </div>
                        </div>
                      </td>

                      {/* Role */}
                      <td className="px-4 py-3.5">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${
                            u.role === 'student'
                              ? 'bg-brand-50 text-brand-700 border-brand-200'
                              : u.role === 'teacher'
                              ? 'bg-growth-50 text-growth-700 border-growth-200'
                              : 'bg-intelligence-50 text-intelligence-700 border-intelligence-200'
                          }`}
                        >
                          {u.role === 'student' ? 'Siswa' : u.role === 'teacher' ? 'Guru' : 'Admin'}
                        </span>
                      </td>

                      {/* Masked ID (Strict Privacy Protection) */}
                      <td className="px-4 py-3.5 font-mono text-[11px] text-slate-600">
                        {u.maskedIdentifier}
                      </td>

                      {/* Class / Title */}
                      <td className="px-4 py-3.5 text-slate-600">
                        {u.className || u.title || '-'}
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3.5">
                        {u.status === 'active' ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-endorse-700 bg-endorse-50 px-2 py-0.5 rounded border border-endorse-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-endorse-500" />
                            <span>Aktif</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-300">
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                            <span>Dinonaktifkan</span>
                          </span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-5 py-3.5 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {/* Edit profile */}
                          <button
                            type="button"
                            onClick={() => handleOpenEdit(u)}
                            className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600 transition-colors"
                            title="Edit Profil"
                            aria-label={`Edit profil ${u.displayName}`}
                          >
                            <Edit className="w-3.5 h-3.5" />
                          </button>

                          {/* Reset password */}
                          <button
                            type="button"
                            onClick={() => {
                              setTargetUser(u);
                              setConfirmAction('reset_password');
                            }}
                            className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600 transition-colors"
                            title="Reset Kata Sandi"
                            aria-label={`Reset kata sandi ${u.displayName}`}
                          >
                            <KeyRound className="w-3.5 h-3.5" />
                          </button>

                          {/* Disable / Reactivate */}
                          {u.status === 'active' ? (
                            <button
                              type="button"
                              onClick={() => {
                                setTargetUser(u);
                                setConfirmAction('disable_account');
                              }}
                              className="p-1.5 rounded-lg border border-reject-200 hover:bg-reject-50 text-reject-600 transition-colors"
                              title="Nonaktifkan Akun"
                              aria-label={`Nonaktifkan akun ${u.displayName}`}
                            >
                              <UserX className="w-3.5 h-3.5" />
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => {
                                setTargetUser(u);
                                setConfirmAction('reactivate_account');
                              }}
                              className="p-1.5 rounded-lg border border-endorse-200 hover:bg-endorse-50 text-endorse-600 transition-colors"
                              title="Aktifkan Kembali Akun"
                              aria-label={`Aktifkan akun ${u.displayName}`}
                            >
                              <UserCheck className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal 1: Create Student */}
        {isStudentModalOpen && (
          <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Tambah Akun Siswa Baru</h3>
                <button
                  type="button"
                  onClick={() => setIsStudentModalOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleCreateStudent} className="space-y-3.5 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Nama Lengkap Siswa</label>
                  <input
                    type="text"
                    required
                    value={studentForm.displayName}
                    onChange={(e) => setStudentForm({ ...studentForm, displayName: e.target.value })}
                    placeholder="Contoh: Alya Pratama"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Nomor Induk Siswa Nasional (NISN)</label>
                  <input
                    type="text"
                    required
                    maxLength={10}
                    value={studentForm.nisn}
                    onChange={(e) => setStudentForm({ ...studentForm, nisn: e.target.value.replace(/\D/g, '') })}
                    placeholder="10 digit NISN (cth: 0012345678)"
                    className="w-full px-3 py-2 font-mono bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
                  />
                  <p className="text-[10px] text-slate-400 mt-1">
                    Angka nol di awal akan tetap dipertahankan. NISN disimpan secara keyed HMAC aman.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Tingkat Kelas</label>
                    <select
                      value={studentForm.gradeLevel}
                      onChange={(e) => setStudentForm({ ...studentForm, gradeLevel: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
                    >
                      <option value="10">Kelas 10 (Fase E)</option>
                      <option value="11">Kelas 11 (Fase F)</option>
                      <option value="12">Kelas 12 (Fase F+)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Rombongan Belajar</label>
                    <select
                      value={studentForm.classId || ''}
                      onChange={(e) => setStudentForm({ ...studentForm, classId: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
                    >
                      <option value="">Pilih Rombel (Opsional)</option>
                      {classes.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setIsStudentModalOpen(false)}
                    className="px-3.5 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold text-xs hover:bg-slate-50"
                  >
                    Batal
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded-xl bg-intelligence-600 hover:bg-intelligence-700 text-white font-semibold text-xs transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? 'Memproses...' : 'Buat Akun Siswa'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal 2: Create Teacher */}
        {isTeacherModalOpen && (
          <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Tambah Akun Guru Validator</h3>
                <button
                  type="button"
                  onClick={() => setIsTeacherModalOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleCreateTeacher} className="space-y-3.5 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Nama Lengkap & Gelar</label>
                  <input
                    type="text"
                    required
                    value={teacherForm.displayName}
                    onChange={(e) => setTeacherForm({ ...teacherForm, displayName: e.target.value })}
                    placeholder="Contoh: Budi Santoso, S.Kom."
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-growth-500"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">NUPTK atau NIP Pendidik</label>
                  <input
                    type="text"
                    required
                    value={teacherForm.identifier}
                    onChange={(e) => setTeacherForm({ ...teacherForm, identifier: e.target.value.replace(/\D/g, '') })}
                    placeholder="16 digit NUPTK atau 18 digit NIP"
                    className="w-full px-3 py-2 font-mono bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-growth-500"
                  />
                  <p className="text-[10px] text-slate-400 mt-1">
                    Sistem mendeteksi NUPTK/NIP otomatis dan menyimpannya secara keyed HMAC.
                  </p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Jabatan / Kompetensi Keahlian</label>
                  <input
                    type="text"
                    value={teacherForm.title || ''}
                    onChange={(e) => setTeacherForm({ ...teacherForm, title: e.target.value })}
                    placeholder="Contoh: Guru Kejuruan Rekayasa Perangkat Lunak"
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-growth-500"
                  />
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setIsTeacherModalOpen(false)}
                    className="px-3.5 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold text-xs hover:bg-slate-50"
                  >
                    Batal
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded-xl bg-growth-600 hover:bg-growth-700 text-white font-semibold text-xs transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? 'Memproses...' : 'Buat Akun Pendidik'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal 3: Edit User Profile */}
        {editingUser && (
          <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Perbarui Profil Pengguna</h3>
                  <p className="text-[11px] text-slate-400 font-mono">{editingUser.maskedIdentifier}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setEditingUser(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleUpdateUser} className="space-y-3.5 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Nama Tampilan</label>
                  <input
                    type="text"
                    required
                    value={editForm.displayName || ''}
                    onChange={(e) => setEditForm({ ...editForm, displayName: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
                  />
                </div>

                {editingUser.role === 'student' && (
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Tingkat Kelas</label>
                    <select
                      value={editForm.gradeLevel || '10'}
                      onChange={(e) => setEditForm({ ...editForm, gradeLevel: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-intelligence-500"
                    >
                      <option value="10">Kelas 10 (Fase E)</option>
                      <option value="11">Kelas 11 (Fase F)</option>
                      <option value="12">Kelas 12 (Fase F+)</option>
                    </select>
                  </div>
                )}

                {editingUser.role === 'teacher' && (
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Gelar / Jabatan</label>
                    <input
                      type="text"
                      value={editForm.title || ''}
                      onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:outline-none focus:ring-2 focus:ring-growth-500"
                    />
                  </div>
                )}

                <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setEditingUser(null)}
                    className="px-3.5 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold text-xs hover:bg-slate-50"
                  >
                    Batal
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-4 py-2 rounded-xl bg-intelligence-600 hover:bg-intelligence-700 text-white font-semibold text-xs transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? 'Menyimpan...' : 'Simpan Perubahan'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal 4: One-Time Credential Modal (Strict Phase 6 Invariant) */}
        {credentialResult && (
          <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4 border border-amber-200">
              <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
                <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
                  <Lock className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Kredensial Sementara Dibuat</h3>
                  <p className="text-[11px] text-slate-500">{credentialResult.displayName} ({credentialResult.maskedIdentifier})</p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-900 space-y-2">
                <p className="text-xs font-semibold">
                  ⚠️ Kata sandi sementara hanya ditampilkan sekali.
                </p>
                <p className="text-[11px] leading-relaxed text-amber-800">
                  Pengguna wajib menggantinya saat login berikutnya sebelum dapat mengakses fitur aplikasi lainnya.
                </p>
              </div>

              <div className="space-y-1.5">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Kata Sandi Sementara (One-Time)
                </span>
                <div className="flex items-center gap-2">
                  <div className="flex-1 p-3 bg-slate-100 rounded-xl font-mono text-base font-bold text-slate-900 tracking-wider select-all border border-slate-200 text-center">
                    {credentialResult.temporaryPassword}
                  </div>
                  <button
                    type="button"
                    onClick={handleCopyPassword}
                    className="p-3 rounded-xl bg-slate-900 text-white hover:bg-slate-800 transition-colors shrink-0"
                    title="Salin Kata Sandi"
                  >
                    {copiedPassword ? <Check className="w-5 h-5 text-endorse-400" /> : <Copy className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setCredentialResult(null)}
                  className="w-full py-2.5 rounded-xl bg-intelligence-600 hover:bg-intelligence-700 text-white font-semibold text-xs transition-colors shadow-xs"
                >
                  Saya Sudah Menyalin / Menutup
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Confirmation Dialog for Sensitive Actions */}
        <ConfirmDialog
          isOpen={!!confirmAction}
          title={
            confirmAction === 'reset_password'
              ? 'Konfirmasi Reset Kata Sandi'
              : confirmAction === 'disable_account'
              ? 'Konfirmasi Penonaktifan Akun'
              : 'Konfirmasi Pengaktifan Kembali Akun'
          }
          description={
            confirmAction === 'reset_password'
              ? `Apakah Anda ingin mereset kata sandi untuk ${targetUser?.displayName}? Kata sandi acak sementara akan dibuat satu kali dan semua sesi aktif pengguna akan dicabut.`
              : confirmAction === 'disable_account'
              ? `Apakah Anda yakin ingin menonaktifkan akun ${targetUser?.displayName}? Pengguna tidak akan dapat login dan seluruh sesi yang berjalan akan dicabut seketika.`
              : `Apakah Anda ingin mengaktifkan kembali akun ${targetUser?.displayName}? Pengguna dapat login kembali menggunakan kredensial aktifnya.`
          }
          confirmLabel={
            confirmAction === 'reset_password'
              ? 'Buat Kata Sandi Sementara'
              : confirmAction === 'disable_account'
              ? 'Ya, Nonaktifkan Akun'
              : 'Ya, Aktifkan Kembali'
          }
          variant={confirmAction === 'disable_account' ? 'danger' : 'warning'}
          onConfirm={handleExecuteAction}
          onCancel={() => {
            setTargetUser(null);
            setConfirmAction(null);
          }}
        />
      </div>
    </AppShell>
  );
}
