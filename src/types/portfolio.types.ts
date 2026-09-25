export type PortfolioStatus = 
  | 'draft' 
  | 'submitted' 
  | 'revision_requested' 
  | 'approved' 
  | 'rejected';

export type ActivityType = 
  | 'project' 
  | 'competition' 
  | 'organization' 
  | 'certification' 
  | 'volunteering' 
  | 'research';

export type EvidenceSourceType = 'file' | 'link';

export interface EvidenceSource {
  type: EvidenceSourceType;
  url: string;
  fileName?: string;
  fileSize?: string;
  mimeType?: string; // 'application/pdf' | 'image/jpeg' | 'image/png' | 'video/mp4'
  platform?: 'github' | 'drive' | 'web' | 'other';
  storageObjectId?: string;
}

export interface ValidationTimelineEvent {
  id: string;
  status: PortfolioStatus;
  actorName: string;
  actorRole: 'student' | 'teacher' | 'system';
  timestamp: string;
  note?: string;
}

export interface PortfolioItem {
  id: string;
  title: string;
  activityType: ActivityType;
  date: string;
  description: string;
  tags: string[]; // 3 to 5 canonical tags
  evidence: EvidenceSource;
  status: PortfolioStatus;
  studentId: string;
  studentName: string;
  studentClass: string;
  currentRevisionId?: string;
  currentRevisionNumber?: number;
  teacherFeedback?: string;
  timeline: ValidationTimelineEvent[];
  createdAt: string;
  updatedAt: string;
}

export interface CanonicalTag {
  id: string;
  label: string;
  category: 'technical' | 'creative' | 'leadership' | 'communication' | 'problem_solving' | 'collaboration';
  description?: string;
}

export interface PortfolioFilter {
  search?: string;
  status?: PortfolioStatus | 'all';
  tag?: string;
  activityType?: ActivityType | 'all';
  sortBy?: 'newest' | 'oldest';
}
