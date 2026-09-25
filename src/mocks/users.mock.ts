import { UserProfile } from '../types/auth.types';

export const MOCK_STUDENT: UserProfile = {
  id: 'usr_std_001',
  name: 'Alya Rahma Azzahra',
  role: 'student',
  email: 'alya.rahma@student.talentra.id',
  schoolName: 'SMA Negeri 1 Teladan Jakarta',
  maskedIdentifier: 'NISN: *******321',
  className: 'XII RPL 1',
  grade: 'Kelas 12',
  avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
};

export const MOCK_TEACHER: UserProfile = {
  id: 'usr_tch_002',
  name: 'Budi Santoso, S.Kom., M.Kom.',
  role: 'teacher',
  email: 'budi.santoso@guru.talentra.id',
  schoolName: 'SMA Negeri 1 Teladan Jakarta',
  maskedIdentifier: 'NIP: *******789',
  title: 'Guru Pembimbing & Validator RPL',
  avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
};

export const MOCK_ADMIN: UserProfile = {
  id: 'usr_adm_003',
  name: 'Dra. Hj. Ratna Juwita, M.Pd.',
  role: 'admin',
  email: 'admin.kurikulum@teladan.sch.id',
  schoolName: 'SMA Negeri 1 Teladan Jakarta',
  maskedIdentifier: 'NPSN: *******543',
  title: 'Koordinator Talenta & Kurikulum Sekolah',
  avatarUrl: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80',
};

export const MOCK_ADMIN_RAIHAN: UserProfile = {
  id: 'usr_adm_raihan',
  name: 'Raihan Ansari',
  role: 'admin',
  email: 'raihanansari6678@gmail.com',
  schoolName: 'SMA Negeri 1 Teladan Jakarta',
  maskedIdentifier: 'EMAIL: *******6678@gmail.com',
  title: 'Administrator Sekolah TALENTRA',
  avatarUrl: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80',
};

export const MOCK_ALL_USERS: UserProfile[] = [
  MOCK_STUDENT,
  {
    id: 'usr_std_002',
    name: 'Bima Perkasa Dewantara',
    role: 'student',
    email: 'bima.perkasa@student.talentra.id',
    schoolName: 'SMA Negeri 1 Teladan Jakarta',
    maskedIdentifier: 'NISN: *******452',
    className: 'XII RPL 1',
    grade: 'Kelas 12',
  },
  {
    id: 'usr_std_003',
    name: 'Citra Dewi Lestari',
    role: 'student',
    email: 'citra.dewi@student.talentra.id',
    schoolName: 'SMA Negeri 1 Teladan Jakarta',
    maskedIdentifier: 'NISN: *******619',
    className: 'XI DKV 2',
    grade: 'Kelas 11',
  },
  {
    id: 'usr_std_004',
    name: 'Dimas Arya Pratama',
    role: 'student',
    email: 'dimas.arya@student.talentra.id',
    schoolName: 'SMA Negeri 1 Teladan Jakarta',
    maskedIdentifier: 'NISN: *******884',
    className: 'XII TKJ 1',
    grade: 'Kelas 12',
  },
  MOCK_TEACHER,
  {
    id: 'usr_tch_003',
    name: 'Sri Wahyuni, S.Pd., M.Hum.',
    role: 'teacher',
    email: 'sri.wahyuni@guru.talentra.id',
    schoolName: 'SMA Negeri 1 Teladan Jakarta',
    maskedIdentifier: 'NUPTK: *******112',
    title: 'Guru Bahasa & Komunikasi Publik',
  },
  MOCK_ADMIN,
  MOCK_ADMIN_RAIHAN,
];
