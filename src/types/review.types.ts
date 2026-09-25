import { PortfolioItem, PortfolioStatus } from './portfolio.types';

export interface SoftSkillRubricDimension {
  id: string;
  name: string;
  description: string;
  levels: Record<1 | 2 | 3 | 4 | 5, string>;
}

export interface RubricAssessment {
  rubricId: string;
  skillName: string;
  score: 1 | 2 | 3 | 4 | 5;
  label: string;
}

export type DecisionAction = 'endorse' | 'request_revision' | 'reject';

export interface ValidationTimelineEntry {
  decisionId: string;
  action: 'approved' | 'revision_requested' | 'rejected';
  feedback?: string | null;
  revisionId: string;
  createdAt?: string | null;
  validatorTitle?: string;
}

export interface ReviewDecisionPayload {
  portfolioId: string;
  revisionId?: string;
  action: DecisionAction;
  feedback?: string;
  rubricRatings?: RubricAssessment[];
  rubricMap?: Record<string, number>;
}

export interface ReviewQueueFilter {
  search?: string;
  className?: string;
  tag?: string;
  status?: PortfolioStatus | 'all';
  sortBy?: 'newest' | 'oldest';
}
