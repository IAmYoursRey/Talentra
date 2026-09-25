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
  login(identifier: string, password?: string): Promise<AuthResult>;
  demoLogin(role: UserRole): Promise<AuthResult>;
  switchRole(role: UserRole): Promise<UserProfile>;
  logout(): Promise<void>;
  subscribeSession(callback: () => void): () => void;
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
  return {
    id: raw.id,
    name: raw.displayName,
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

  public async getCurrentSession(): Promise<SessionState> {
    if (this.isLoaded && this.inMemoryUser) {
      return {
        isAuthenticated: true,
        user: this.inMemoryUser,
        role: this.inMemoryUser.role,
      };
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

    // Standalone fallback for demo logins
    const fallbackUser =
      role === 'student' ? MOCK_STUDENT : role === 'teacher' ? MOCK_TEACHER : MOCK_ADMIN;
    this.inMemoryUser = { ...fallbackUser };
    this.isLoaded = true;
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

    this.inMemoryUser = null;
    this.isLoaded = false;
    this.notify();
  }
}

export const authService: IAuthService = new AuthService();
