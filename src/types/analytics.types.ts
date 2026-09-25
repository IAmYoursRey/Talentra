export interface TalentHeatmapItem {
  category: string;
  percentage: number;
  studentCount: number;
  growth: number; // percentage change
  topSkills: string[];
}

export interface TalentTrendPoint {
  cohort: string; // e.g. "2024/2025 Ganjil", "2024/2025 Genap", "2025/2026 Ganjil"
  technology: number;
  creative: number;
  leadership: number;
  communication: number;
  research: number;
}

export interface SchoolMetrics {
  totalActiveStudents: number;
  totalValidators: number;
  validatedPortfolios: number;
  completionRate: number; // 0 - 100 percentage
  pendingReviewsCount: number;
}

export interface ClassSummary {
  id: string;
  name: string;
  grade: string;
  major: string;
  homeroomTeacher: string;
  studentsCount: number;
  assignedValidators: string[];
  validatedCount: number;
}

export interface TalentHeatmapDimension {
  dimension: string;
  displayName: string;
  eligibleStudents?: number;
  studentsWithEvidence?: number;
  coverageRate?: number;
  meanEvidenceIndex?: number;
  suppressed: boolean;
  reason?: string;
}

export interface TalentHeatmapResponse {
  analyticsVersion: string;
  generatedAt: string;
  suppressed: boolean;
  reason?: string;
  cohortSize: number | null;
  dimensions: TalentHeatmapDimension[];
}

export interface SchoolRubricAggregate {
  dimensionCode: string;
  averageScore?: number;
  assessmentCount?: number;
  uniqueStudentCount?: number;
  suppressed: boolean;
  reason?: string;
}

export interface ValidationMetricsResponse {
  analyticsVersion: string;
  generatedAt: string;
  totalActiveStudents: number;
  activeTeacherValidators: number;
  submittedAwaitingValidation: number;
  approvedCount: number;
  revisionRequestedCount: number;
  rejectedCount: number;
  completedDecisions: number;
  validationCompletionRate: number;
  medianTurnaroundHours: number;
}
