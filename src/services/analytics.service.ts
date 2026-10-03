import {
  SchoolMetrics,
  TalentHeatmapItem,
  TalentTrendPoint,
  ClassSummary,
  TalentHeatmapResponse,
  SchoolRubricAggregate,
  ValidationMetricsResponse,
} from '../types/analytics.types';
import { MOCK_SCHOOL_METRICS, MOCK_TALENT_HEATMAP, MOCK_TALENT_TRENDS, MOCK_CLASSES } from '../mocks/analytics.mock';
import { mockAppState } from './mock-state';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export interface AnalyticsFilterParams {
  academicYear?: string;
  gradeLevel?: string;
  classId?: string;
  from?: string;
  to?: string;
}

export interface IAnalyticsService {
  getSchoolMetrics(): Promise<SchoolMetrics>;
  getTalentHeatmap(cohort?: string): Promise<TalentHeatmapItem[]>;
  getRealTalentHeatmap(filters?: AnalyticsFilterParams): Promise<TalentHeatmapResponse>;
  getSchoolRubrics(filters?: AnalyticsFilterParams): Promise<{
    analyticsVersion: string;
    generatedAt: string;
    suppressed: boolean;
    reason?: string;
    aggregates: SchoolRubricAggregate[];
  }>;
  getValidationMetrics(filters?: AnalyticsFilterParams): Promise<ValidationMetricsResponse>;
  getTalentTrends(): Promise<TalentTrendPoint[]>;
  getClassesSummary(): Promise<ClassSummary[]>;
}

class AnalyticsService implements IAnalyticsService {
  public async getSchoolMetrics(): Promise<SchoolMetrics> {
    try {
      const res = await fetch(`${API_BASE}/api/v1/admin/analytics/overview`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(1000),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          totalActiveStudents: data.totalActiveStudents,
          totalValidators: data.activeTeacherValidators,
          validatedPortfolios: data.approvedInPeriod,
          completionRate: data.validationCompletionRate,
          pendingReviewsCount: data.submittedAwaitingValidation,
        };
      }
    } catch {
      // Backend unavailable; fallback
    }

    const items = mockAppState.getPortfolioItems();
    const approvedCount = items.filter((i) => i.status === 'approved').length;
    const submittedCount = items.filter((i) => i.status === 'submitted').length;

    return {
      ...MOCK_SCHOOL_METRICS,
      validatedPortfolios: MOCK_SCHOOL_METRICS.validatedPortfolios + approvedCount - 3,
      pendingReviewsCount: submittedCount,
    };
  }

  public async getRealTalentHeatmap(filters?: AnalyticsFilterParams): Promise<TalentHeatmapResponse> {
    try {
      const params = new URLSearchParams();
      if (filters?.academicYear && filters.academicYear !== 'all') params.append('academicYear', filters.academicYear);
      if (filters?.gradeLevel && filters.gradeLevel !== 'all') params.append('gradeLevel', filters.gradeLevel);
      if (filters?.classId && filters.classId !== 'all') params.append('classId', filters.classId);

      const res = await fetch(`${API_BASE}/api/v1/admin/analytics/talent?${params.toString()}`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(1000),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Backend unavailable; fallback
    }

    // Default fallback structured as TalentHeatmapResponse
    return {
      analyticsVersion: 'school-talent-v1',
      generatedAt: new Date().toISOString(),
      suppressed: false,
      cohortSize: 36,
      dimensions: [
        {
          dimension: 'digital-literacy',
          displayName: 'Literasi Digital',
          eligibleStudents: 36,
          studentsWithEvidence: 28,
          coverageRate: 77.8,
          meanEvidenceIndex: 58.3,
          suppressed: false,
        },
        {
          dimension: 'problem-solving',
          displayName: 'Pemecahan Masalah',
          eligibleStudents: 36,
          studentsWithEvidence: 24,
          coverageRate: 66.7,
          meanEvidenceIndex: 50.0,
          suppressed: false,
        },
        {
          dimension: 'creativity',
          displayName: 'Kreativitas & Inovasi',
          eligibleStudents: 36,
          studentsWithEvidence: 22,
          coverageRate: 61.1,
          meanEvidenceIndex: 44.4,
          suppressed: false,
        },
        {
          dimension: 'collaboration',
          displayName: 'Kolaborasi & Kerja Tim',
          eligibleStudents: 36,
          studentsWithEvidence: 20,
          coverageRate: 55.6,
          meanEvidenceIndex: 41.7,
          suppressed: false,
        },
        {
          dimension: 'communication',
          displayName: 'Komunikasi Profesional',
          eligibleStudents: 36,
          studentsWithEvidence: 19,
          coverageRate: 52.8,
          meanEvidenceIndex: 38.9,
          suppressed: false,
        },
        {
          dimension: 'leadership',
          displayName: 'Inisiatif & Kepemimpinan',
          eligibleStudents: 36,
          studentsWithEvidence: 15,
          coverageRate: 41.7,
          meanEvidenceIndex: 30.6,
          suppressed: false,
        },
      ],
    };
  }

  public async getSchoolRubrics(filters?: AnalyticsFilterParams): Promise<{
    analyticsVersion: string;
    generatedAt: string;
    suppressed: boolean;
    reason?: string;
    aggregates: SchoolRubricAggregate[];
  }> {
    try {
      const params = new URLSearchParams();
      if (filters?.academicYear && filters.academicYear !== 'all') params.append('academicYear', filters.academicYear);
      if (filters?.gradeLevel && filters.gradeLevel !== 'all') params.append('gradeLevel', filters.gradeLevel);
      if (filters?.classId && filters.classId !== 'all') params.append('classId', filters.classId);

      const res = await fetch(`${API_BASE}/api/v1/admin/analytics/rubrics?${params.toString()}`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(1000),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Backend unavailable; fallback
    }

    return {
      analyticsVersion: 'school-rubric-v1',
      generatedAt: new Date().toISOString(),
      suppressed: false,
      aggregates: [
        { dimensionCode: 'initiative', averageScore: 4.2, assessmentCount: 24, uniqueStudentCount: 18, suppressed: false },
        { dimensionCode: 'collaboration', averageScore: 4.5, assessmentCount: 26, uniqueStudentCount: 19, suppressed: false },
        { dimensionCode: 'communication', averageScore: 3.9, assessmentCount: 22, uniqueStudentCount: 17, suppressed: false },
        { dimensionCode: 'responsibility', averageScore: 4.4, assessmentCount: 25, uniqueStudentCount: 18, suppressed: false },
        { dimensionCode: 'resilience', averageScore: 4.1, assessmentCount: 20, uniqueStudentCount: 16, suppressed: false },
      ],
    };
  }

  public async getValidationMetrics(filters?: AnalyticsFilterParams): Promise<ValidationMetricsResponse> {
    try {
      const params = new URLSearchParams();
      if (filters?.academicYear && filters.academicYear !== 'all') params.append('academicYear', filters.academicYear);
      if (filters?.gradeLevel && filters.gradeLevel !== 'all') params.append('gradeLevel', filters.gradeLevel);
      if (filters?.classId && filters.classId !== 'all') params.append('classId', filters.classId);

      const res = await fetch(`${API_BASE}/api/v1/admin/analytics/validation?${params.toString()}`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(1000),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // fallback
    }

    return {
      analyticsVersion: 'school-validation-v1',
      generatedAt: new Date().toISOString(),
      totalActiveStudents: 36,
      activeTeacherValidators: 4,
      submittedAwaitingValidation: 3,
      approvedCount: 12,
      revisionRequestedCount: 2,
      rejectedCount: 1,
      completedDecisions: 15,
      validationCompletionRate: 83.3,
      medianTurnaroundHours: 24.5,
    };
  }

  public async getTalentHeatmap(_cohort?: string): Promise<TalentHeatmapItem[]> {
    return [...MOCK_TALENT_HEATMAP];
  }

  public async getTalentTrends(): Promise<TalentTrendPoint[]> {
    return [...MOCK_TALENT_TRENDS];
  }

  public async getClassesSummary(): Promise<ClassSummary[]> {
    return [...MOCK_CLASSES];
  }
}

export const analyticsService: IAnalyticsService = new AnalyticsService();

