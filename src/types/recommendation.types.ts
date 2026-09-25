export interface RecommendationComponentScores {
  radarMatch: number;
  tagMatch: number;
  rubricMatch: number;
}

export interface RecommendationContributor {
  portfolioId: string;
  title: string;
  approvedAt?: string;
  tags?: string[];
}

export interface SupportingDimension {
  dimension: string;
  score: number;
}

export interface RecommendationPath {
  id: string;
  code: string;
  title: string;
  cluster: string;
  description: string;
  type: 'career' | 'study';
  matchScore: number;
  components: RecommendationComponentScores;
  supportingDimensions: SupportingDimension[];
  supportingTags: string[];
  evidenceCount: number;
  supportingPortfolios: RecommendationContributor[];
  suggestedPathways: string[];
  rationale: string;
}

export interface RecommendationEvidenceConfidence {
  score: number;
  level: 'limited' | 'developing' | 'moderate' | 'strong';
  approvedPortfolioCount: number;
  distinctDimensionCount: number;
  timeSpanMonths: number;
  rubricAssessmentCount: number;
  activePeriodCount: number;
}

export interface RecommendationResponse {
  snapshotId?: string;
  generatedAt: string;
  scoringVersion: string;
  catalogVersion: string;
  mappingVersion: string;
  isStale?: boolean;
  evidenceConfidence: RecommendationEvidenceConfidence;
  careerPaths: RecommendationPath[];
  studyPaths: RecommendationPath[];
  disclaimer: string;
}

export interface ProfessionalDescriptionResponse {
  documentId: string;
  portfolioId: string;
  revisionId: string;
  originalTitle: string;
  originalDescription: string;
  professionalText: string;
  translatorVersion: string;
  mode: string;
  generatedAt: string;
}

// Backward compatibility alias for any existing legacy components
export interface SupportingSkill {
  name: string;
  relevanceScore: number;
}

export interface CareerStudyRecommendation {
  id: string;
  title: string;
  category: 'study' | 'career';
  fieldCluster: string;
  matchPercentage: number;
  supportingSkills: SupportingSkill[];
  evidenceCount: number;
  evidenceTitles: string[];
  rationale: string;
  suggestedPathways: string[];
  isDemoData: boolean;
}
