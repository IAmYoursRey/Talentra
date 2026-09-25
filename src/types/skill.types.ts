export interface SkillRadarPoint {
  skill: string;
  score: number; // 0 - 100
  fullMark: number;
  approvedEvidenceCount: number;
  dimensionCode?: string;
}

export interface SkillContributor {
  portfolioId: string;
  portfolioTitle: string;
  date: string;
  contributionScore: number;
  activityType: string;
  tags?: string[];
}

export interface SkillDetail {
  skillName: string;
  score: number;
  category: string;
  approvedEvidenceCount: number;
  contributors: SkillContributor[];
  rubricNotes?: string[];
}

export interface TeacherRubricObservation {
  dimensionCode: string;
  displayName: string;
  averageScore: number;
  assessmentCount: number;
}

export interface SkillSnapshot {
  scoringVersion: string;
  radarPoints: SkillRadarPoint[];
  topSkills: { name: string; score: number; level: string }[];
  totalApprovedEvidence: number;
  lastCalculatedAt: string;
  teacherRubrics?: TeacherRubricObservation[];
}
