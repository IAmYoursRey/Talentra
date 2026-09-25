export type VerificationStatus = 'verified' | 'expired' | 'revoked' | 'invalid' | 'invalid_token';

export interface PublicVerifiedProject {
  title: string;
  activityType: string;
  activityDate?: string;
  description: string;
  tags?: string[];
}

export interface PublicVerifiedSkill {
  name: string;
  score: number;
  level?: string;
}

export interface PublicVerificationResult {
  status: VerificationStatus;
  displayCode?: string;
  studentDisplayName?: string;
  schoolDisplayName?: string;
  issuedAt?: string;
  expiresAt?: string | null;
  revokedAt?: string | null;
  snapshotDigestShort?: string;
  selectedPortfolioSummaries?: PublicVerifiedProject[];
  validatedSkillSummary?: PublicVerifiedSkill[];
  verificationStatement?: string;
  message?: string;
}
