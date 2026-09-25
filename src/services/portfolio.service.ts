import { PortfolioItem, PortfolioFilter, CanonicalTag, EvidenceSource, ValidationTimelineEvent } from '../types/portfolio.types';
import { mockAppState } from './mock-state';
import { MOCK_CANONICAL_TAGS } from '../mocks/canonical-tags.mock';

export interface IPortfolioService {
  getPortfolioItems(filter?: PortfolioFilter): Promise<PortfolioItem[]>;
  getPortfolioItemById(id: string): Promise<PortfolioItem | null>;
  getCanonicalTags(): Promise<CanonicalTag[]>;
  createPortfolioItem(data: Omit<PortfolioItem, 'id' | 'timeline' | 'createdAt' | 'updatedAt'>): Promise<PortfolioItem>;
  resubmitRevision(id: string, updatedFields: Partial<PortfolioItem>): Promise<PortfolioItem>;
  subscribePortfolio(callback: () => void): () => void;
  requestUploadIntent?(portfolioId: string, filename: string, contentType: string, sizeBytes: number): Promise<{ storageObjectId: string; uploadUrl: string }>;
  completeUpload?(portfolioId: string, storageObjectId: string): Promise<any>;
  getEvidenceDownloadAccess?(portfolioId: string, storageObjectId: string): Promise<{ downloadUrl: string }>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function mapDocToPortfolioItem(doc: any): PortfolioItem {
  const evidenceRefs = doc.evidence_refs || [];
  let evidence: EvidenceSource = {
    type: 'file',
    url: '#',
    fileName: 'Lampiran Karya',
    fileSize: '1.0 MB',
  };

  if (evidenceRefs.length > 0) {
    const primary = evidenceRefs[0];
    if (primary.type === 'file') {
      const sizeMB = primary.size_bytes ? `${(primary.size_bytes / (1024 * 1024)).toFixed(1)} MB` : undefined;
      evidence = {
        type: 'file',
        url: '#',
        fileName: primary.display_name || 'Berkas Karya',
        fileSize: sizeMB,
        mimeType: primary.file_type,
        storageObjectId: primary.storage_object_id,
      };
    } else if (primary.type === 'external_link') {
      const url = primary.url || '';
      const platform = url.includes('github') ? 'github' : url.includes('drive') ? 'drive' : 'web';
      evidence = {
        type: 'link',
        url: url,
        platform,
      };
    }
  }

  const timeline: ValidationTimelineEvent[] = [
    {
      id: `evt-1-${doc.portfolio_id}`,
      status: 'draft',
      actorName: 'Siswa',
      actorRole: 'student',
      timestamp: doc.created_at || new Date().toISOString(),
      note: 'Draf portofolio dibuat',
    },
  ];

  if (doc.status === 'submitted' || doc.status === 'approved' || doc.status === 'revision_requested') {
    timeline.push({
      id: `evt-2-${doc.portfolio_id}`,
      status: 'submitted',
      actorName: 'Siswa',
      actorRole: 'student',
      timestamp: doc.submitted_at || doc.updated_at || new Date().toISOString(),
      note: 'Diajukan untuk validasi guru pembimbing',
    });
  }

  return {
    id: doc.portfolio_id,
    title: doc.title || '',
    activityType: doc.activity_type || 'project',
    date: doc.activity_date || new Date().toISOString().split('T')[0],
    description: doc.description || '',
    tags: doc.canonical_tag_ids || [],
    evidence,
    status: doc.status || 'draft',
    studentId: doc.student_id || 'usr_std_001',
    studentName: 'Alya Rahma Azzahra',
    studentClass: 'XII RPL 1',
    teacherFeedback: doc.teacher_feedback,
    timeline,
    createdAt: doc.created_at || new Date().toISOString(),
    updatedAt: doc.updated_at || new Date().toISOString(),
  };
}

class HTTPPortfolioService implements IPortfolioService {
  private listeners: Set<() => void> = new Set();

  private notify() {
    this.listeners.forEach((cb) => {
      try {
        cb();
      } catch (e) {
        // ignore subscriber exceptions
      }
    });
  }

  public async getCanonicalTags(): Promise<CanonicalTag[]> {
    try {
      const res = await fetch(`${API_BASE}/api/v1/skill-tags`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      if (res.ok) {
        const data = await res.json();
        if (data.items && Array.isArray(data.items)) {
          return data.items.map((item: any) => ({
            id: item.code,
            label: item.label,
            category: item.category,
            description: item.description,
          }));
        }
      }
    } catch (e) {
      // Fallback gracefully to mock tags
    }
    return [...MOCK_CANONICAL_TAGS];
  }

  public async getPortfolioItems(filter?: PortfolioFilter): Promise<PortfolioItem[]> {
    try {
      const params = new URLSearchParams();
      if (filter) {
        if (filter.status && filter.status !== 'all') params.append('status', filter.status);
        if (filter.tag && filter.tag !== 'all') params.append('tag', filter.tag);
        if (filter.activityType && filter.activityType !== 'all') params.append('activityType', filter.activityType);
        if (filter.search && filter.search.trim()) params.append('search', filter.search.trim());
        if (filter.sortBy) params.append('sortBy', filter.sortBy);
      }

      const res = await fetch(`${API_BASE}/api/v1/student/portfolio?${params.toString()}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });

      if (res.ok) {
        const data = await res.json();
        if (data.items && Array.isArray(data.items)) {
          return data.items.map(mapDocToPortfolioItem);
        }
      }
    } catch (e) {
      // Fallback to mock state if backend not running
    }

    // Mock fallback
    let items = mockAppState.getPortfolioItems();
    const currentUser = mockAppState.getCurrentUser();
    if (currentUser.role === 'student') {
      items = items.filter((item) => item.studentId === currentUser.id);
    }
    if (filter) {
      if (filter.status && filter.status !== 'all') {
        items = items.filter((item) => item.status === filter.status);
      }
      if (filter.tag) {
        items = items.filter((item) => item.tags.includes(filter.tag!));
      }
      if (filter.activityType && filter.activityType !== 'all') {
        items = items.filter((item) => item.activityType === filter.activityType);
      }
      if (filter.search && filter.search.trim()) {
        const query = filter.search.toLowerCase().trim();
        items = items.filter(
          (item) =>
            item.title.toLowerCase().includes(query) ||
            item.description.toLowerCase().includes(query) ||
            item.tags.some((t) => t.toLowerCase().includes(query))
        );
      }
      if (filter.sortBy === 'oldest') {
        items = [...items].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      } else {
        items = [...items].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
      }
    }
    return items;
  }

  public async getPortfolioItemById(id: string): Promise<PortfolioItem | null> {
    try {
      const res = await fetch(`${API_BASE}/api/v1/student/portfolio/${id}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });

      if (res.ok) {
        const doc = await res.json();
        return mapDocToPortfolioItem(doc);
      }
    } catch (e) {
      // Fallback
    }
    const mockItem = mockAppState.getPortfolioItemById(id);
    return mockItem || null;
  }

  public async createPortfolioItem(
    data: Omit<PortfolioItem, 'id' | 'timeline' | 'createdAt' | 'updatedAt'>
  ): Promise<PortfolioItem> {
    if (data.tags.length < 3 || data.tags.length > 5) {
      throw new Error('Portofolio wajib memiliki antara 3 hingga 5 tag kompetensi kanonikal.');
    }

    try {
      const evidencePayload =
        data.evidence.type === 'file'
          ? {
              type: 'file',
              storageObjectId: data.evidence.storageObjectId,
              fileName: data.evidence.fileName,
              fileSize: data.evidence.fileSize,
              mimeType: data.evidence.mimeType,
            }
          : {
              type: 'external_link',
              url: data.evidence.url,
              label: 'Tautan Proyek',
            };

      const res = await fetch(`${API_BASE}/api/v1/student/portfolio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': `create-${Date.now()}-${Math.random().toString(36).substring(7)}`,
        },
        credentials: 'include',
        body: JSON.stringify({
          title: data.title,
          activityType: data.activityType,
          activityDate: data.date,
          description: data.description,
          canonicalTagIds: data.tags,
          evidence: evidencePayload,
        }),
      });

      if (res.ok) {
        const doc = await res.json();
        const portfolioId = doc.portfolio_id;

        // If requested to submit directly
        if (data.status === 'submitted') {
          const submitRes = await fetch(`${API_BASE}/api/v1/student/portfolio/${portfolioId}/submit`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Idempotency-Key': `submit-${portfolioId}`,
            },
            credentials: 'include',
          });
          if (submitRes.ok) {
            const submittedDoc = await submitRes.json();
            this.notify();
            return mapDocToPortfolioItem(submittedDoc);
          } else {
            const err = await submitRes.json();
            throw new Error(err?.error?.message || 'Gagal mengajukan karya untuk validasi.');
          }
        }

        this.notify();
        return mapDocToPortfolioItem(doc);
      } else {
        const err = await res.json();
        throw new Error(err?.error?.message || 'Gagal menyimpan draf portofolio di server.');
      }
    } catch (e: any) {
      if (e.message && e.message.includes('Portofolio')) {
        throw e;
      }
      // If network fails entirely, fall back to mock
      const item = mockAppState.addPortfolioItem(data);
      this.notify();
      return item;
    }
  }

  public async resubmitRevision(id: string, updatedFields: Partial<PortfolioItem>): Promise<PortfolioItem> {
    if (updatedFields.tags && (updatedFields.tags.length < 3 || updatedFields.tags.length > 5)) {
      throw new Error('Portofolio wajib memiliki antara 3 hingga 5 tag kompetensi.');
    }

    try {
      // 1. Begin revision cycle
      await fetch(`${API_BASE}/api/v1/student/portfolio/${id}/revision`, {
        method: 'POST',
        credentials: 'include',
      });

      // 2. Update editable fields
      const patchPayload: any = {};
      if (updatedFields.title) patchPayload.title = updatedFields.title;
      if (updatedFields.description) patchPayload.description = updatedFields.description;
      if (updatedFields.tags) patchPayload.canonicalTagIds = updatedFields.tags;
      if (updatedFields.activityType) patchPayload.activityType = updatedFields.activityType;

      await fetch(`${API_BASE}/api/v1/student/portfolio/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(patchPayload),
      });

      // 3. Submit revision
      const res = await fetch(`${API_BASE}/api/v1/student/portfolio/${id}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': `resubmit-${id}-${Date.now()}`,
        },
        credentials: 'include',
      });

      if (res.ok) {
        const doc = await res.json();
        this.notify();
        return mapDocToPortfolioItem(doc);
      }
    } catch (e) {
      // Fallback
    }

    const result = mockAppState.resubmitPortfolio(id, updatedFields);
    if (!result) throw new Error('Portofolio tidak ditemukan.');
    this.notify();
    return result;
  }

  public async requestUploadIntent(
    portfolioId: string,
    filename: string,
    contentType: string,
    sizeBytes: number
  ): Promise<{ storageObjectId: string; uploadUrl: string }> {
    const res = await fetch(`${API_BASE}/api/v1/student/portfolio/${portfolioId}/uploads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        filename,
        contentType,
        sizeBytes,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err?.error?.message || 'Gagal mendaftarkan izin unggah berkas.');
    }
    const data = await res.json();
    return {
      storageObjectId: data.storageObjectId,
      uploadUrl: data.uploadUrl,
    };
  }

  public async completeUpload(portfolioId: string, storageObjectId: string): Promise<any> {
    const res = await fetch(
      `${API_BASE}/api/v1/student/portfolio/${portfolioId}/uploads/${storageObjectId}/complete`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      }
    );

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err?.error?.message || 'Validasi berkas gagal pada server.');
    }
    return await res.json();
  }

  public async getEvidenceDownloadAccess(
    portfolioId: string,
    storageObjectId: string
  ): Promise<{ downloadUrl: string }> {
    const res = await fetch(
      `${API_BASE}/api/v1/student/portfolio/${portfolioId}/evidence/${storageObjectId}/access`,
      {
        method: 'GET',
        credentials: 'include',
      }
    );

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err?.error?.message || 'Gagal memperoleh tautan unduh bukti karya.');
    }
    return await res.json();
  }

  public subscribePortfolio(callback: () => void): () => void {
    this.listeners.add(callback);
    const mockUnsub = mockAppState.subscribe(callback);
    return () => {
      this.listeners.delete(callback);
      mockUnsub();
    };
  }
}

export const portfolioService: IPortfolioService = new HTTPPortfolioService();
