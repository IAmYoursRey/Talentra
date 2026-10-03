import {
  AdminUser,
  AdminUserListResponse,
  CreateStudentPayload,
  CreateTeacherPayload,
  UpdateUserProfilePayload,
  UserCredentialResult,
} from '../types/admin.types';
import { MOCK_ALL_USERS } from '../mocks/users.mock';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

function getCsrfToken(): string {
  if (typeof document !== 'undefined') {
    const match = document.cookie.match(/(?:^|;\s*)talentra_csrf=([^;]+)/);
    if (match) return match[1];
  }
  return '';
}

async function ensureCsrfToken(): Promise<string> {
  const existing = getCsrfToken();
  if (existing) return existing;
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/csrf`, {
      credentials: 'include',
    });
    if (res.ok) {
      const data = await res.json();
      return data.csrfToken || '';
    }
  } catch {
    // fallback
  }
  return '';
}

export interface IAdminUserService {
  getCachedUsers(filters?: {
    role?: string;
    status?: string;
    classId?: string;
    gradeLevel?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): AdminUser[];
  listUsers(filters?: {
    role?: string;
    status?: string;
    classId?: string;
    gradeLevel?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<AdminUserListResponse>;
  getUser(userId: string): Promise<AdminUser | null>;
  createStudent(payload: CreateStudentPayload): Promise<UserCredentialResult>;
  createTeacher(payload: CreateTeacherPayload): Promise<UserCredentialResult>;
  updateUser(userId: string, payload: UpdateUserProfilePayload): Promise<AdminUser>;
  disableUser(userId: string): Promise<{ success: boolean; message: string }>;
  reactivateUser(userId: string): Promise<{ success: boolean; message: string }>;
  resetPassword(userId: string): Promise<UserCredentialResult>;
}

class AdminUserServiceImpl implements IAdminUserService {
  public async listUsers(filters?: {
    role?: string;
    status?: string;
    classId?: string;
    gradeLevel?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<AdminUserListResponse> {
    try {
      const params = new URLSearchParams();
      if (filters?.role && filters.role !== 'all') params.append('role', filters.role);
      if (filters?.status && filters.status !== 'all') params.append('status', filters.status);
      if (filters?.classId && filters.classId !== 'all') params.append('classId', filters.classId);
      if (filters?.gradeLevel && filters.gradeLevel !== 'all') params.append('gradeLevel', filters.gradeLevel);
      if (filters?.search && filters.search.trim()) params.append('search', filters.search.trim());
      if (filters?.limit) params.append('limit', String(filters.limit));
      if (filters?.offset) params.append('offset', String(filters.offset));

      if (typeof window !== 'undefined' && !window.navigator.onLine) {
        throw new Error('Offline');
      }

      const res = await fetch(`${API_BASE}/api/v1/admin/users?${params.toString()}`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(200),
      });

      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Backend unavailable or offline; fallback to mock
    }

    return this.getCachedUsers(filters).length ? {
      items: this.getCachedUsers(filters),
      total: this.getCachedUsers(filters).length,
      limit: filters?.limit || 50,
      offset: filters?.offset || 0,
    } : {
      items: [],
      total: 0,
      limit: filters?.limit || 50,
      offset: filters?.offset || 0,
    };
  }

  public getCachedUsers(filters?: {
    role?: string;
    status?: string;
    classId?: string;
    gradeLevel?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): AdminUser[] {
    let items: AdminUser[] = MOCK_ALL_USERS.map((u) => ({
      id: u.id,
      schoolId: 'sch-smkn1-cibinong',
      role: u.role,
      status: 'active',
      displayName: u.name,
      email: u.email,
      maskedIdentifier: u.maskedIdentifier,
      className: u.className,
      gradeLevel: u.className ? u.className.split(' ')[0] : '12',
      title: u.title,
      mustChangePassword: false,
    }));

    if (filters?.role && filters.role !== 'all') {
      items = items.filter((u) => u.role === filters.role);
    }
    if (filters?.status && filters.status !== 'all') {
      items = items.filter((u) => u.status === filters.status);
    }
    if (filters?.classId && filters.classId !== 'all') {
      items = items.filter((u) => u.className === filters.classId);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter(
        (u) =>
          u.displayName.toLowerCase().includes(q) ||
          u.email.toLowerCase().includes(q) ||
          u.maskedIdentifier.toLowerCase().includes(q)
      );
    }
    return items;
  }

  public async getUser(userId: string): Promise<AdminUser | null> {
    try {
      const res = await fetch(`${API_BASE}/api/v1/admin/users/${userId}`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Accept': 'application/json' },
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // fallback
    }

    const fallback = MOCK_ALL_USERS.find((u) => u.id === userId);
    if (!fallback) return null;
    return {
      id: fallback.id,
      schoolId: 'sch-smkn1-cibinong',
      role: fallback.role,
      status: 'active',
      displayName: fallback.name,
      email: fallback.email,
      maskedIdentifier: fallback.maskedIdentifier,
      className: fallback.className,
      title: fallback.title,
      mustChangePassword: false,
    };
  }

  public async createStudent(payload: CreateStudentPayload): Promise<UserCredentialResult> {
    const csrfToken = await ensureCsrfToken();
    const res = await fetch(`${API_BASE}/api/v1/admin/users/students`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CSRF-Token': csrfToken,
      },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      const data = await res.json();
      return {
        id: data.id,
        displayName: data.displayName,
        maskedIdentifier: data.maskedIdentifier,
        role: 'student',
        temporaryPassword: data.temporaryPassword,
        message: 'Akun siswa berhasil dibuat.',
      };
    }

    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || 'Gagal membuat akun siswa.');
  }

  public async createTeacher(payload: CreateTeacherPayload): Promise<UserCredentialResult> {
    const csrfToken = await ensureCsrfToken();
    const res = await fetch(`${API_BASE}/api/v1/admin/users/teachers`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CSRF-Token': csrfToken,
      },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      const data = await res.json();
      return {
        id: data.id,
        displayName: data.displayName,
        maskedIdentifier: data.maskedIdentifier,
        role: 'teacher',
        temporaryPassword: data.temporaryPassword,
        message: 'Akun pendidik berhasil dibuat.',
      };
    }

    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || 'Gagal membuat akun pendidik.');
  }

  public async updateUser(userId: string, payload: UpdateUserProfilePayload): Promise<AdminUser> {
    const csrfToken = await ensureCsrfToken();
    const res = await fetch(`${API_BASE}/api/v1/admin/users/${userId}`, {
      method: 'PATCH',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CSRF-Token': csrfToken,
      },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      return await res.json();
    }

    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || 'Gagal memperbarui profil pengguna.');
  }

  public async disableUser(userId: string): Promise<{ success: boolean; message: string }> {
    const csrfToken = await ensureCsrfToken();
    const res = await fetch(`${API_BASE}/api/v1/admin/users/${userId}/disable`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CSRF-Token': csrfToken,
      },
    });

    if (res.ok) {
      return await res.json();
    }

    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || 'Gagal menonaktifkan pengguna.');
  }

  public async reactivateUser(userId: string): Promise<{ success: boolean; message: string }> {
    const csrfToken = await ensureCsrfToken();
    const res = await fetch(`${API_BASE}/api/v1/admin/users/${userId}/reactivate`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CSRF-Token': csrfToken,
      },
    });

    if (res.ok) {
      return await res.json();
    }

    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || 'Gagal mengaktifkan kembali pengguna.');
  }

  public async resetPassword(userId: string): Promise<UserCredentialResult> {
    const csrfToken = await ensureCsrfToken();
    const res = await fetch(`${API_BASE}/api/v1/admin/users/${userId}/reset-password`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CSRF-Token': csrfToken,
      },
    });

    if (res.ok) {
      const data = await res.json();
      return {
        id: userId,
        displayName: 'Pengguna',
        maskedIdentifier: '',
        role: 'user',
        temporaryPassword: data.temporaryPassword,
        message: data.message,
      };
    }

    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || 'Gagal mengatur ulang kata sandi.');
  }
}

export const adminUserService: IAdminUserService = new AdminUserServiceImpl();
