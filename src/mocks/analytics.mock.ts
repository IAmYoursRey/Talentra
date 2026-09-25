import { SchoolMetrics, TalentHeatmapItem, TalentTrendPoint, ClassSummary } from '../types/analytics.types';

export const MOCK_SCHOOL_METRICS: SchoolMetrics = {
  totalActiveStudents: 842,
  totalValidators: 48,
  validatedPortfolios: 1264,
  completionRate: 91.4,
  pendingReviewsCount: 14,
};

export const MOCK_TALENT_HEATMAP: TalentHeatmapItem[] = [
  {
    category: 'Teknologi & Komputasi',
    percentage: 38,
    studentCount: 320,
    growth: 12.5,
    topSkills: ['Web Development', 'IoT & Robotics', 'Problem Solving', 'Data Analysis'],
  },
  {
    category: 'Kreatif & Desain Visual',
    percentage: 26,
    studentCount: 219,
    growth: 8.2,
    topSkills: ['UI/UX Design', 'Graphic Design', 'Video Editing'],
  },
  {
    category: 'Kepemimpinan & Organisasi',
    percentage: 18,
    studentCount: 152,
    growth: 5.4,
    topSkills: ['Leadership', 'Event Management', 'Teamwork'],
  },
  {
    category: 'Komunikasi & Bahasa',
    percentage: 16,
    studentCount: 135,
    growth: 3.1,
    topSkills: ['Public Speaking', 'Writing', 'Debate'],
  },
  {
    category: 'Riset & Pemikiran Kritis',
    percentage: 12,
    studentCount: 101,
    growth: 15.0,
    topSkills: ['Research', 'Critical Thinking', 'Scientific Writing'],
  },
  {
    category: 'Kewirausahaan Digital',
    percentage: 9,
    studentCount: 76,
    growth: 6.8,
    topSkills: ['Product Strategy', 'Digital Marketing', 'Financial Literacy'],
  },
];

export const MOCK_TALENT_TRENDS: TalentTrendPoint[] = [
  { cohort: '2024/2025 Ganjil', technology: 28, creative: 22, leadership: 20, communication: 18, research: 8 },
  { cohort: '2024/2025 Genap', technology: 32, creative: 24, leadership: 19, communication: 17, research: 10 },
  { cohort: '2025/2026 Ganjil', technology: 35, creative: 25, leadership: 18, communication: 16, research: 11 },
  { cohort: '2025/2026 Genap', technology: 38, creative: 26, leadership: 18, communication: 16, research: 12 },
];

export const MOCK_CLASSES: ClassSummary[] = [
  {
    id: 'cls_001',
    name: 'XII RPL 1',
    grade: 'Kelas 12',
    major: 'Rekayasa Perangkat Lunak',
    homeroomTeacher: 'Budi Santoso, S.Kom., M.Kom.',
    studentsCount: 36,
    assignedValidators: ['Budi Santoso, M.Kom.', 'Sri Wahyuni, M.Hum.'],
    validatedCount: 94,
  },
  {
    id: 'cls_002',
    name: 'XII RPL 2',
    grade: 'Kelas 12',
    major: 'Rekayasa Perangkat Lunak',
    homeroomTeacher: 'Agus Setiawan, S.Kom.',
    studentsCount: 35,
    assignedValidators: ['Agus Setiawan, S.Kom.'],
    validatedCount: 88,
  },
  {
    id: 'cls_003',
    name: 'XI DKV 1',
    grade: 'Kelas 11',
    major: 'Desain Komunikasi Visual',
    homeroomTeacher: 'Nurul Hidayati, S.Sn.',
    studentsCount: 34,
    assignedValidators: ['Nurul Hidayati, S.Sn.', 'Budi Santoso, M.Kom.'],
    validatedCount: 76,
  },
  {
    id: 'cls_004',
    name: 'XI DKV 2',
    grade: 'Kelas 11',
    major: 'Desain Komunikasi Visual',
    homeroomTeacher: 'Farhan Maulana, M.Ds.',
    studentsCount: 36,
    assignedValidators: ['Farhan Maulana, M.Ds.'],
    validatedCount: 82,
  },
  {
    id: 'cls_005',
    name: 'XII TKJ 1',
    grade: 'Kelas 12',
    major: 'Teknik Komputer & Jaringan',
    homeroomTeacher: 'Hendra Wijaya, S.Pd.',
    studentsCount: 35,
    assignedValidators: ['Hendra Wijaya, S.Pd.'],
    validatedCount: 91,
  },
];
