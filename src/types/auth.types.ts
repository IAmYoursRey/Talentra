export type UserRole = 'student' | 'teacher' | 'admin';

export interface UserProfile {
  id: string;
  name: string;
  role: UserRole;
  email: string;
  avatarUrl?: string;
  schoolName: string;
  maskedIdentifier: string; // e.g. "NISN: *******321" or "NIP: *******789"
  className?: string; // for students
  grade?: string;
  title?: string; // for teachers/admin, e.g. "Guru Pembimbing RPL"
}

export interface SessionState {
  isAuthenticated: boolean;
  user: UserProfile | null;
  role: UserRole;
}
