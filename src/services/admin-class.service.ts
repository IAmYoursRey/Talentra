import {
  AdminClass,
  AdminClassDetail,
  CreateClassPayload,
  UpdateClassPayload,
  EnrolledStudent,
  AssignedTeacher,
} from '../types/admin.types';

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

export interface IAdminClassService {
  listClasses(filters?: {
    academicYear?: string;
    gradeLevel?: string;
    status?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<AdminClass[]>;
  getClass(classId: string): Promise<AdminClassDetail | null>;
  createClass(payload: CreateClassPayload): Promise<AdminClass>;
  updateClass(classId: string, payload: UpdateClassPayload): Promise<AdminClass>;
  archiveClass(classId: string): Promise<{ success: boolean; message: string }>;
  enrollStudent(classId: string, studentId: string): Promise<{ success: boolean; message: string }>;
  unenrollStudent(classId: string, studentId: string): Promise<{ success: boolean; message: string }>;
  assignTeacher(classId: string, teacherId: string, assignmentType?: string): Promise<{ success: boolean; message: string }>;
  removeTeacherAssignment(classId: string, teacherId: string): Promise<{ success: boolean; message: string }>;
}

const FALLBACK_CLASSES: AdminClass[] = [
  {
    id: 'cls-xii-rpl-1',
    schoolId: 'sch-smkn1-cibinong',
    name: 'XII RPL 1',
    gradeLevel: '12',
    academicYear: '2025/2026',
    status: 'active',
    studentsCount: 36,
    validatorsCount: 2,
    createdAt: '2025-07-15T00:00:00Z',
  },
  {
    id: 'cls-xii-rpl-2',
    schoolId: 'sch-smkn1-cibinong',
    name: 'XII RPL 2',
    gradeLevel: '12',
    academicYear: '2025/2026',
    status: 'active',
    studentsCount: 35,
    validatorsCount: 2,
    createdAt: '2025-07-15T00:00:00Z',
  },
  {
    id: 'cls-xi-rpl-1',
    schoolId: 'sch-smkn1-cibinong',
    name: 'XI RPL 1',
    gradeLevel: '11',
    academicYear: '2025/2026',
    status: 'active',
    studentsCount: 36,
    validatorsCount: 1,
    createdAt: '2025-07-15T00:00:00Z',
  },
];

class AdminClassServiceImpl implements IAdminClassService {
  public async listClasses(filters?: {
    academicYear?: string;
    gradeLevel?: string;
    status?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<AdminClass[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.academicYear && filters.academicYear !== 'all') params.append('academicYear', filters.academicYear);
      if (filters?.gradeLevel && filters.gradeLevel !== 'all') params.append('gradeLevel', filters.gradeLevel);
      if (filters?.status && filters.status !== 'all') params.append('status', filters.status);
      if (filters?.search && filters.search.trim()) params.append('search', filters.search.trim());
      if (filters?.limit) params.append('limit', String(filters.limit));
      if (filters?.offset) params.append('offset', String(filters.offset));

      const res = await fetch(`${API_BASE}/api/v1/admin/classes?${params.toString()}`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Accept': 'application/json' },
      });

      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Backend unavailable; fallback
    }

    let items = [...FALLBACK_CLASSES];
    if (filters?.gradeLevel && filters.gradeLevel !== 'all') {
      items = items.filter((c) => c.gradeLevel === filters.gradeLevel);
    }
    if (filters?.status && filters.status !== 'all') {
      items = items.filter((c) => c.status === filters.status);
    }
    if (filters?.search && filters.search.trim()) {
      const q = filters.search.toLowerCase().trim();
      items = items.filter((c) => c.name.toLowerCase().includes(q));
    }
    return items;
  }

  public async getClass(classId: string): Promise<AdminClassDetail | null> {
    try {
      const res = await fetch(`${API_BASE}/api/v1/admin/classes/${classId}`, {
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

    const cls = FALLBACK_CLASSES.find((c) => c.id === classId);
    if (!cls) return null;
    return {
      ...cls,
      students: [],
      teachers: [],
    };
  }

  public async createClass(payload: CreateClassPayload): Promise<AdminClass> {
    const csrfToken = await ensureCsrfToken();
    const res = await fetch(`${API_BASE}/api/v1/admin/classes`, {
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
      return await res.json();
    }

    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || 'Gagal membuat rombongan belajar.');
  }

  public async updateClass(classId: string, payload: UpdateClassPayload): Promise<AdminClass> {
    const csrfToken = await ensureCsrfToken();
    const res = await fetch(`${API_BASE}/api/v1/admin/classes/${classId}`, {
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
    throw new Error(err.error?.message || 'Gagal memperbarui rombongan belajar.');
  }

  public async archiveClass(classId: string): Promise<{ success: boolean; message: string }> {
    const csrfToken = await ensureCsrfToken();
    const res = await fetch(`${API_BASE}/api/v1/admin/classes/${classId}/archive`, {
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
    throw new Error(err.error?.message || 'Gagal mengarsipkan rombongan belajar.');
  }

  public async enrollStudent(classId: string, studentId: string): Promise<{ success: boolean; message: string }> {
    const csrfToken = await ensureCsrfToken();
    const res = await fetch(`${API_BASE}/api/v1/admin/classes/${classId}/students`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CSRF-Token': csrfToken,
      },
      body: JSON.stringify({ studentId }),
    });

    if (res.ok) {
      return await res.json();
    }

    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || 'Gagal mendaftarkan siswa ke kelas.');
  }

  public async unenrollStudent(classId: string, studentId: string): Promise<{ success: boolean; message: string }> {
    const csrfToken = await ensureCsrfToken();
    const res = await fetch(`${API_BASE}/api/v1/admin/classes/${classId}/students/${studentId}`, {
      method: 'DELETE',
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
    throw new Error(err.error?.message || 'Gagal mengeluarkan siswa dari kelas.');
  }

  public async assignTeacher(classId: string, teacherId: string, assignmentType: string = 'validator'): Promise<{ success: boolean; message: string }> {
    const csrfToken = await ensureCsrfToken();
    const res = await fetch(`${API_BASE}/api/v1/admin/classes/${classId}/teachers`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CSRF-Token': csrfToken,
      },
      body: JSON.stringify({ teacherId, assignmentType }),
    });

    if (res.ok) {
      return await res.json();
    }

    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || 'Gagal menugaskan guru ke kelas.');
  }

  public async removeTeacherAssignment(classId: string, teacherId: string): Promise<{ success: boolean; message: string }> {
    const csrfToken = await ensureCsrfToken();
    const res = await fetch(`${API_BASE}/api/v1/admin/classes/${classId}/teachers/${teacherId}`, {
      method: 'DELETE',
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
    throw new Error(err.error?.message || 'Gagal menghapus penugasan guru.');
  }
}

export const adminClassService: IAdminClassService = new AdminClassServiceImpl();
