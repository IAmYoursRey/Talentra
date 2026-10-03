import { UserProfile, UserRole, SessionState } from '../types/auth.types';
import {
  MOCK_STUDENT,
  MOCK_TEACHER,
  MOCK_ADMIN,
  MOCK_ADMIN_RAIHAN,
} from '../mocks/users.mock';

export interface AuthResult {
  user: UserProfile;
  redirectTo: string;
}

export interface IAuthService {
  getCurrentSession(): Promise<SessionState>;
  getCurrentUser(): UserProfile | null;
  login(identifier: string, password?: string): Promise<AuthResult>;
  demoLogin(role: UserRole): Promise<AuthResult>;
  switchRole(role: UserRole): Promise<UserProfile>;
  logout(): Promise<void>;
  subscribeSession(callback: () => void): () => void;
  changePassword(currentPassword: string, newPassword: string): Promise<{ success: boolean; message: string }>;
}

function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/(?:^|;\s*)talentra_csrf=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

interface ApiUserResponse {
  id: string;
  displayName: string;
  role: UserRole;
  email: string;
  school: {
    id: string;
    name: string;
  };
  maskedIdentifier: string;
  className?: string | null;
  title?: string | null;
}

function mapUserResponseToProfile(raw: ApiUserResponse): UserProfile {
  let displayName = raw.displayName;
  if (displayName === 'Raihan Ansari' || raw.email === 'raihanansari6678@gmail.com') {
    displayName = 'Admin Demo';
  }
  return {
    id: raw.id,
    name: displayName,
    role: raw.role,
    email: raw.email,
    schoolName: raw.school?.name || 'Sekolah TALENTRA',
    maskedIdentifier: raw.maskedIdentifier || '',
    className: raw.className || undefined,
    title: raw.title || undefined,
  };
}

class AuthService implements IAuthService {
  private inMemoryUser: UserProfile | null = null;
  private isLoaded = false;
  private subscribers: Set<() => void> = new Set();

  private notify() {
    this.subscribers.forEach((cb) => {
      try {
        cb();
      } catch {
        // Ignore subscriber execution error
      }
    });
  }

  public subscribeSession(callback: () => void): () => void {
    this.subscribers.add(callback);
    return () => {
      this.subscribers.delete(callback);
    };
  }

  public getCurrentUser(): UserProfile | null {
    return this.inMemoryUser;
  }

  public async getCurrentSession(): Promise<SessionState> {
    if (this.isLoaded && this.inMemoryUser) {
      return {
        isAuthenticated: true,
        user: this.inMemoryUser,
        role: this.inMemoryUser.role,
      };
    }

    // Check for demo session cookie for seamless online prototype navigation
    if (typeof document !== 'undefined') {
      const demoMatch = document.cookie.match(/(?:^|;\s*)talentra_session=demo_session_([^;]+)/);
      if (demoMatch) {
        const role = demoMatch[1] as UserRole;
        if (['student', 'teacher', 'admin'].includes(role)) {
          const fallbackUser =
            role === 'student' ? MOCK_STUDENT : role === 'teacher' ? MOCK_TEACHER : MOCK_ADMIN;
          this.inMemoryUser = { ...fallbackUser };
          this.isLoaded = true;
          return {
            isAuthenticated: true,
            user: this.inMemoryUser,
            role: this.inMemoryUser.role,
          };
        }
      }
    }

    try {
      const res = await fetch('/api/v1/auth/me', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });

      if (!res.ok) {
        this.inMemoryUser = null;
        this.isLoaded = true;
        return {
          isAuthenticated: false,
          user: null,
          role: 'student',
        };
      }

      const data = (await res.json()) as ApiUserResponse;
      this.inMemoryUser = mapUserResponseToProfile(data);
      this.isLoaded = true;

      return {
        isAuthenticated: true,
        user: this.inMemoryUser,
        role: this.inMemoryUser.role,
      };
    } catch {
      this.inMemoryUser = null;
      this.isLoaded = true;
      return {
        isAuthenticated: false,
        user: null,
        role: 'student',
      };
    }
  }

  public async login(identifier: string, password: string = ''): Promise<AuthResult> {
    const trimmedId = identifier.trim().toLowerCase();

    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ identifier, password }),
      });

      if (!res.ok) {
        if (res.status >= 500) {
          if (
            trimmedId === 'raihanansari6678@gmail.com' &&
            password === 'raihanansari6678@gmail.com'
          ) {
            this.inMemoryUser = { ...MOCK_ADMIN_RAIHAN };
            this.isLoaded = true;
            this.notify();
            return {
              user: this.inMemoryUser,
              redirectTo: '/admin',
            };
          }
        }
        const errData = await res.json().catch(() => null);
        const message =
          errData?.error?.message || errData?.detail?.message || 'ID pengguna atau kata sandi tidak sesuai.';
        throw new Error(message);
      }

      const data = await res.json();
      this.inMemoryUser = mapUserResponseToProfile(data.user);
      this.isLoaded = true;
      this.notify();

      return {
        user: this.inMemoryUser,
        redirectTo: data.redirectTo,
      };
    } catch (err: unknown) {
      // In offline / standalone development fallback, check Raihan admin credentials
      if (
        trimmedId === 'raihanansari6678@gmail.com' &&
        password === 'raihanansari6678@gmail.com'
      ) {
        this.inMemoryUser = { ...MOCK_ADMIN_RAIHAN };
        this.isLoaded = true;
        this.notify();
        return {
          user: this.inMemoryUser,
          redirectTo: '/admin',
        };
      }
      throw err;
    }
  }

  public async demoLogin(role: UserRole): Promise<AuthResult> {
    // 1. Attempt authoritative authenticated login using provisioned database credentials
    const canonicalCredentials: Record<UserRole, { identifier: string; password: string }> = {
      student: { identifier: '0081234567', password: 'PasswordSiswa123!' },
      teacher: { identifier: '198501012010011001', password: 'PasswordGuru123!' },
      admin: { identifier: 'raihanansari6678@gmail.com', password: 'raihanansari6678@gmail.com' },
    };

    const targetCred = canonicalCredentials[role];
    if (targetCred) {
      try {
        return await this.login(targetCred.identifier, targetCred.password);
      } catch {
        // Fall through to legacy demo-login or mock fallback if offline
      }
    }

    try {
      const res = await fetch('/api/v1/auth/demo-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ role }),
      });

      if (res.ok) {
        const data = await res.json();
        this.inMemoryUser = mapUserResponseToProfile(data.user);
        this.isLoaded = true;
        this.notify();

        return {
          user: this.inMemoryUser,
          redirectTo: data.redirectTo,
        };
      }
    } catch {
      // Fallback below
    }

    // Standalone fallback for offline mock demos
    const fallbackUser =
      role === 'student' ? MOCK_STUDENT : role === 'teacher' ? MOCK_TEACHER : MOCK_ADMIN;
    this.inMemoryUser = { ...fallbackUser };
    this.isLoaded = true;

    if (typeof document !== 'undefined') {
      document.cookie = `talentra_session=demo_session_${role}; path=/; max-age=604800; samesite=lax`;
    }

    this.notify();

    return {
      user: this.inMemoryUser!,
      redirectTo: `/${role}`,
    };
  }

  public async switchRole(role: UserRole): Promise<UserProfile> {
    const result = await this.demoLogin(role);
    return result.user;
  }

  public async logout(): Promise<void> {
    let csrf = getCsrfToken();
    if (!csrf) {
      try {
        const csrfRes = await fetch('/api/v1/auth/csrf', { credentials: 'include' });
        if (csrfRes.ok) {
          const csrfData = await csrfRes.json();
          csrf = csrfData.csrfToken;
        }
      } catch {
        // Fallback
      }
    }

    try {
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(csrf ? { 'X-CSRF-Token': csrf } : {}),
        },
        credentials: 'include',
      });
    } catch {
      // Incurred network or server error during logout
    }

    if (typeof document !== 'undefined') {
      document.cookie = 'talentra_session=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    }

    this.inMemoryUser = null;
    this.isLoaded = false;
    this.notify();
  }

  public async changePassword(
    currentPassword: string,
    newPassword: string
  ): Promise<{ success: boolean; message: string }> {
    let csrf = getCsrfToken();
    if (!csrf) {
      try {
        const csrfRes = await fetch('/api/v1/auth/csrf', { credentials: 'include' });
        if (csrfRes.ok) {
          const csrfData = await csrfRes.json();
          csrf = csrfData.csrfToken;
        }
      } catch {
        // Fallback
      }
    }

    const res = await fetch('/api/v1/auth/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...(csrf ? { 'X-CSRF-Token': csrf } : {}),
      },
      credentials: 'include',
      body: JSON.stringify({ currentPassword, newPassword }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      const msg = errData.error?.message || errData.detail?.message || `Gagal mengubah kata sandi (HTTP ${res.status})`;
      throw new Error(msg);
    }

    const data = await res.json();
    return {
      success: true,
      message: data.message || 'Kata sandi berhasil diperbarui.',
    };
  }
}

export const authService: IAuthService = new AuthService();
