export interface AdminUser {
  id: string;
  schoolId: string;
  role: 'student' | 'teacher' | 'admin';
  status: 'active' | 'disabled';
  displayName: string;
  email: string;
  maskedIdentifier: string;
  className?: string | null;
  gradeLevel?: string | null;
  title?: string | null;
  mustChangePassword: boolean;
  createdAt?: string | null;
}

export interface AdminUserListResponse {
  items: AdminUser[];
  total: number;
  limit: number;
  offset: number;
}

export interface CreateStudentPayload {
  displayName: string;
  nisn: string;
  gradeLevel: string | number;
  classId?: string;
}

export interface CreateTeacherPayload {
  displayName: string;
  identifier: string;
  title?: string;
}

export interface UpdateUserProfilePayload {
  displayName?: string;
  gradeLevel?: string | number;
  title?: string;
}

export interface UserCredentialResult {
  id: string;
  displayName: string;
  maskedIdentifier: string;
  role: string;
  temporaryPassword?: string;
  message?: string;
}

export interface AdminClass {
  id: string;
  schoolId: string;
  name: string;
  gradeLevel: string;
  academicYear: string;
  status: 'active' | 'archived';
  studentsCount: number;
  validatorsCount: number;
  createdAt?: string | null;
}

export interface EnrolledStudent {
  id: string;
  displayName: string;
  status: string;
  gradeLevel?: string;
  maskedIdentifier: string;
}

export interface AssignedTeacher {
  id: string;
  displayName: string;
  title?: string;
  assignmentType: string;
}

export interface AdminClassDetail extends AdminClass {
  students: EnrolledStudent[];
  teachers: AssignedTeacher[];
}

export interface CreateClassPayload {
  name: string;
  gradeLevel: string | number;
  academicYear: string;
}

export interface UpdateClassPayload {
  name?: string;
  gradeLevel?: string | number;
  academicYear?: string;
}
