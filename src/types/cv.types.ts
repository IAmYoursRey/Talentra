export interface CVValidatedSkill {
  dimension?: string;
  name: string;
  score: number;
  level?: string;
}

export interface CVApprovedPortfolio {
  portfolioId: string;
  revisionId?: string;
  title: string;
  activityType: string;
  activityDate: string;
  description: string;
  professionalDescription?: string | null;
  canonicalTagIds: string[];
  status?: string;
}

export interface CVTeacherCompetency {
  dimension: string;
  score?: number;
  count?: number;
  summary: string;
}

export interface CVExplorationOptions {
  available: boolean;
  careerInterests: string[];
  studyInterests: string[];
}

export interface IssuedCVVersion {
  snapshotId: string;
  displayCode: string;
  status: 'active' | 'revoked' | 'expired';
  issuedAt: string;
  expiresAt: string | null;
  selectedProjectCount: number;
  fingerprint: string;
}

export interface CVBuilderContext {
  profile: {
    displayName: string;
    schoolName: string;
    className: string;
  };
  approvedPortfolios: CVApprovedPortfolio[];
  validatedSkills: CVValidatedSkill[];
  teacherCompetencies: CVTeacherCompetency[];
  explorationOptions: CVExplorationOptions | null;
  existingVersions: IssuedCVVersion[];
  policy: {
    minSelectedPortfolios: number;
    maxSelectedPortfolios: number;
    verificationTtlDays: number | null;
  };
}

export interface CVGenerateRequest {
  portfolioIds: string[];
  includeTeacherCompetencies: boolean;
  includeExploration: boolean;
}

export interface CVGenerateResponse {
  snapshotId: string;
  displayCode: string;
  verificationToken?: string;
  verificationUrl?: string;
  issuedAt: string;
  expiresAt: string | null;
  contentDigest: string;
  fingerprint: string;
  status: string;
  selectedProjectCount: number;
  message?: string;
}

export interface CVDetailSnapshot {
  snapshotId: string;
  snapshotVersion: string;
  displayCode: string;
  status: string;
  generatedAt: string;
  profile: {
    display_name: string;
    school_name: string;
    class_name?: string;
    professional_summary: string;
  };
  approvedSkills: Array<{ dimension?: string; name: string; score: number; level?: string }>;
  teacherValidatedCompetencies: Array<{ dimension: string; score?: number; summary: string }>;
  selectedPortfolios: Array<{
    portfolio_id: string;
    revision_id?: string;
    title: string;
    activity_type: string;
    activity_date: string;
    description: string;
    professional_description?: string;
    tags: string[];
  }>;
  optionalExplorationSummary?: {
    career_interests?: string[];
    study_interests?: string[];
  } | null;
  contentDigest: string;
  fingerprint: string;
}
