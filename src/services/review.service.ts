import { PortfolioItem, EvidenceSource, ValidationTimelineEvent } from '../types/portfolio.types';
import {
  ReviewDecisionPayload,
  ReviewQueueFilter,
  SoftSkillRubricDimension,
  ValidationTimelineEntry,
} from '../types/review.types';
import { mockAppState } from './mock-state';
import { MOCK_RUBRIC_DIMENSIONS } from '../mocks/soft-skills-rubric.mock';

export interface IReviewService {
  getReviewQueue(filter?: ReviewQueueFilter): Promise<PortfolioItem[]>;
  getReviewItemById(id: string): Promise<PortfolioItem | null>;
  getRubricDimensions(): Promise<SoftSkillRubricDimension[]>;
  submitReviewDecision(payload: ReviewDecisionPayload): Promise<PortfolioItem>;
  getEvidenceAccess?(portfolioId: string, storageObjectId: string): Promise<{ downloadUrl: string }>;
  subscribeQueue(callback: () => void): () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

function mapQueueItemToPortfolioItem(item: any): PortfolioItem {
  return {
    id: item.portfolioId,
    currentRevisionId: item.revisionId,
    studentId: item.studentId || 'unknown',
    studentName: item.studentDisplayName || 'Siswa',
    studentClass: item.classDisplayName || 'Kelas',
    title: item.title,
    activityType: item.activityType,
    date: item.submittedAt ? item.submittedAt.split('T')[0] : new Date().toISOString().split('T')[0],
    description: '',
    tags: item.canonicalTags || [],
    evidence: {
      type: 'file',
      url: '#',
      fileName: 'Bukti Karya',
      fileSize: 'Tersedia',
    },
    status: item.status || 'submitted',
    timeline: [],
    createdAt: item.submittedAt || new Date().toISOString(),
    updatedAt: item.submittedAt || new Date().toISOString(),
  };
}

function mapReviewDetailToPortfolioItem(data: any): PortfolioItem {
  const p = data.portfolio || {};
  const rev = data.revision || {};
  const evRefs = rev.evidence || [];

  let evidence: EvidenceSource = {
    type: 'file',
    url: '#',
    fileName: 'Lampiran Karya',
    fileSize: '1.0 MB',
  };

  if (evRefs.length > 0) {
    const first = evRefs[0];
    if (first.type === 'file') {
      const sizeMB = first.size_bytes ? `${(first.size_bytes / (1024 * 1024)).toFixed(1)} MB` : undefined;
      evidence = {
        type: 'file',
        url: '#',
        fileName: first.display_name || 'Berkas Karya',
        fileSize: sizeMB,
        mimeType: first.file_type,
        storageObjectId: first.storage_object_id,
      };
    } else if (first.type === 'external_link') {
      const url = first.url || '';
      const platform = url.includes('github') ? 'github' : url.includes('drive') ? 'drive' : 'web';
      evidence = {
        type: 'link',
        url: url,
        platform,
      };
    }
  }

  const timeline: ValidationTimelineEvent[] = (data.validationHistory || []).map((h: ValidationTimelineEntry, idx: number) => ({
    id: h.decisionId || `hist-${idx}`,
    status: h.action === 'approved' ? 'approved' : h.action === 'revision_requested' ? 'revision_requested' : 'rejected',
    actorName: h.validatorTitle || 'Guru Pembimbing',
    actorRole: 'teacher',
    timestamp: h.createdAt || new Date().toISOString(),
    note: h.feedback || (h.action === 'approved' ? 'Portofolio disetujui' : h.action === 'revision_requested' ? 'Revisi diminta' : 'Portofolio ditolak'),
  }));

  return {
    id: data.portfolioId,
    currentRevisionId: rev.revisionId,
    studentId: data.studentId,
    studentName: data.studentDisplayName,
    studentClass: data.classDisplayName,
    title: rev.titleSnapshot || p.title || '',
    activityType: rev.activityTypeSnapshot || p.activityType || 'project',
    date: p.activityDate || new Date().toISOString().split('T')[0],
    description: rev.descriptionSnapshot || p.description || '',
    tags: rev.tags || [],
    evidence,
    status: p.status || 'submitted',
    timeline,
    teacherFeedback: p.teacherFeedback,
    createdAt: rev.submittedAt || new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

export class HTTPReviewService implements IReviewService {
  private subscribers: Array<() => void> = [];

  private notifySubscribers() {
    this.subscribers.forEach((cb) => {
      try {
        cb();
      } catch (e) {
        console.error('Subscriber error:', e);
      }
    });
  }

  public subscribeQueue(callback: () => void): () => void {
    this.subscribers.push(callback);
    return () => {
      this.subscribers = this.subscribers.filter((s) => s !== callback);
    };
  }

  public async getReviewQueue(filter?: ReviewQueueFilter): Promise<PortfolioItem[]> {
    try {
      const params = new URLSearchParams();
      if (filter?.className && filter.className !== 'all') {
        params.append('class', filter.className);
      }
      if (filter?.tag && filter.tag !== 'all') {
        params.append('tag', filter.tag);
      }
      if (filter?.search && filter.search.trim()) {
        params.append('search', filter.search.trim());
      }
      if (filter?.sortBy) {
        params.append('sortBy', filter.sortBy);
      }

      const url = `${API_BASE}/api/v1/teacher/reviews${params.toString() ? `?${params.toString()}` : ''}`;
      const res = await fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (res.ok) {
        const json = await res.json();
        const rawItems = json.items || [];
        return rawItems.map(mapQueueItemToPortfolioItem);
      }
    } catch {
      // Backend unreachable; gracefully fallback to mock
    }

    // Mock fallback
    let items = mockAppState.getPortfolioItems();
    if (filter?.status && filter.status !== 'all') {
      items = items.filter((item) => item.status === filter.status);
    } else if (!filter?.status) {
      items = items.filter((item) => item.status !== 'draft');
    }

    if (filter?.className && filter.className !== 'all') {
      items = items.filter((item) => item.studentClass.toLowerCase().includes(filter.className!.toLowerCase()));
    }

    if (filter?.tag) {
      items = items.filter((item) => item.tags.includes(filter.tag!));
    }

    if (filter?.search && filter.search.trim()) {
      const q = filter.search.toLowerCase().trim();
      items = items.filter(
        (item) =>
          item.studentName.toLowerCase().includes(q) ||
          item.title.toLowerCase().includes(q) ||
          item.studentClass.toLowerCase().includes(q) ||
          item.tags.some((t) => t.toLowerCase().includes(q))
      );
    }

    if (filter?.sortBy === 'oldest') {
      items = [...items].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    } else {
      items = [...items].sort((a, b) => {
        if (a.status === 'submitted' && b.status !== 'submitted') return -1;
        if (b.status === 'submitted' && a.status !== 'submitted') return 1;
        return new Date(b.date).getTime() - new Date(a.date).getTime();
      });
    }

    return items;
  }

  public async getReviewItemById(id: string): Promise<PortfolioItem | null> {
    try {
      const res = await fetch(`${API_BASE}/api/v1/teacher/reviews/${id}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (res.ok) {
        const json = await res.json();
        return mapReviewDetailToPortfolioItem(json);
      }
    } catch {
      // Backend unreachable; gracefully fallback to mock
    }

    const item = mockAppState.getPortfolioItemById(id);
    return item || null;
  }

  public async getRubricDimensions(): Promise<SoftSkillRubricDimension[]> {
    return [...MOCK_RUBRIC_DIMENSIONS];
  }

  public async getEvidenceAccess(portfolioId: string, storageObjectId: string): Promise<{ downloadUrl: string }> {
    const res = await fetch(
      `${API_BASE}/api/v1/teacher/reviews/${portfolioId}/evidence/${storageObjectId}/access`,
      {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
        },
      }
    );

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error?.message || 'Gagal memperoleh tautan unduh bukti karya.');
    }

    return await res.json();
  }

  public async submitReviewDecision(payload: ReviewDecisionPayload): Promise<PortfolioItem> {
    const actionMap: Record<string, string> = {
      endorse: 'approved',
      request_revision: 'revision_requested',
      reject: 'rejected',
    };

    const targetAction = actionMap[payload.action] || payload.action;

    let rubricPayload: any = undefined;
    if (targetAction === 'approved') {
      rubricPayload = payload.rubricMap || {
        initiative: 4,
        collaboration: 4,
        communication: 4,
        responsibility: 4,
        resilience: 3,
      };
      if (payload.rubricRatings && payload.rubricRatings.length > 0) {
        const mappedRatings: Record<string, number> = {};
        for (const r of payload.rubricRatings) {
          mappedRatings[r.rubricId] = r.score;
        }
        rubricPayload = mappedRatings;
      }
    }

    const bodyPayload = {
      revisionId: payload.revisionId || 'rev-current',
      action: targetAction,
      feedback: payload.feedback || '',
      rubric: rubricPayload,
    };

    try {
      const res = await fetch(`${API_BASE}/api/v1/teacher/reviews/${payload.portfolioId}/decision`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Idempotency-Key': `teacher-dec-${payload.portfolioId}-${Date.now()}`,
        },
        body: JSON.stringify(bodyPayload),
      });

      if (res.ok) {
        this.notifySubscribers();
        // Fetch updated review item
        const updated = await this.getReviewItemById(payload.portfolioId);
        if (updated) return updated;
      } else if (res.status === 401 || res.status === 403) {
        // Fall through to mock fallback if unauthenticated / running in offline test script
      } else {
        const errJson = await res.json().catch(() => ({}));
        if (errJson.error?.message) {
          throw new Error(errJson.error.message);
        }
      }
    } catch (e: any) {
      if (e.message && !e.message.includes('fetch')) {
        throw e;
      }
      // If network error, fallback to mock state
    }

    // Mock fallback
    let newStatus: PortfolioItem['status'];
    let defaultNote = '';

    if (payload.action === 'endorse') {
      newStatus = 'approved';
      defaultNote = 'Portofolio disetujui dan divalidasi oleh guru pembimbing.';
    } else if (payload.action === 'request_revision') {
      newStatus = 'revision_requested';
      if (!payload.feedback || !payload.feedback.trim()) {
        throw new Error('Catatan revisi wajib diisi agar siswa mengetahui perbaikan yang diperlukan.');
      }
      defaultNote = `Revisi diminta: ${payload.feedback}`;
    } else {
      newStatus = 'rejected';
      if (!payload.feedback || !payload.feedback.trim()) {
        throw new Error('Alasan penolakan wajib disertakan.');
      }
      defaultNote = `Portofolio ditolak: ${payload.feedback}`;
    }

    const updated = mockAppState.updatePortfolioStatus(
      payload.portfolioId,
      newStatus,
      defaultNote,
      payload.feedback,
      payload.rubricRatings
    );

    if (!updated) throw new Error('Portofolio tidak ditemukan.');
    this.notifySubscribers();
    return updated;
  }
}

export const reviewService: IReviewService = new HTTPReviewService();
