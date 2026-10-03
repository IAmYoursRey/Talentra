import {
  RecommendationResponse,
  ProfessionalDescriptionResponse,
} from '../types/recommendation.types';
import { ensureCsrfToken } from '../lib/csrf';

export interface IRecommendationService {
  getCachedRecommendations(): RecommendationResponse;
  getStudentRecommendations(forceRefresh?: boolean): Promise<RecommendationResponse>;
  refreshStudentRecommendations(): Promise<RecommendationResponse>;
  generateProfessionalDescription(portfolioId: string, forceRegenerate?: boolean): Promise<ProfessionalDescriptionResponse>;
  getProfessionalDescription(portfolioId: string): Promise<ProfessionalDescriptionResponse>;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window === 'undefined' ? (process.env.API_BASE_URL || 'http://127.0.0.1:8000') : '');

export class HTTPRecommendationService implements IRecommendationService {
  public getCachedRecommendations(): RecommendationResponse {
    return {
      snapshotId: 'rec_snap_demo',
      generatedAt: new Date().toISOString(),
      scoringVersion: '2.0.0',
      catalogVersion: '2026.1',
      mappingVersion: '1.4.0',
      evidenceConfidence: {
        score: 88,
        level: 'strong',
        approvedPortfolioCount: 12,
        distinctDimensionCount: 5,
        timeSpanMonths: 14,
        rubricAssessmentCount: 6,
        activePeriodCount: 3,
      },
      careerPaths: [
        {
          id: 'rec_cp_01',
          code: 'CP-SWE',
          title: 'Software & Web Engineer',
          cluster: 'Teknologi Informasi & Rekayasa Perangkat Lunak',
          description: 'Pengembangan arsitektur web modern, API terukur, dan solusi fullstack inovatif.',
          type: 'career',
          matchScore: 92,
          components: { radarMatch: 94, tagMatch: 90, rubricMatch: 92 },
          supportingDimensions: [
            { dimension: 'Pemrograman Web', score: 92 },
            { dimension: 'Problem Solving', score: 88 },
          ],
          supportingTags: ['tag-web-02', 'tag-problem-04'],
          evidenceCount: 5,
          supportingPortfolios: [
            { portfolioId: 'p-1', title: 'Sistem Monitoring Limbah IoT & Web' },
            { portfolioId: 'p-2', title: 'Aplikasi Presensi Siswa QR Code Dinamis' },
          ],
          suggestedPathways: [
            'Program Studi S1 Sistem Informasi / Ilmu Komputer',
            'Fullstack Web Developer, Software Engineer, Cloud Architect',
          ],
          rationale: 'Berdasarkan bukti karya pengembangan sistem web dan logika algoritma teruji di lingkungan sekolah.',
        },
        {
          id: 'rec_cp_02',
          code: 'CP-UID',
          title: 'Product & UI/UX Designer',
          cluster: 'Desain Interaksi & Media Kreatif',
          description: 'Perancangan pengalaman pengguna, prototyping interaktif, dan riset desain terapan.',
          type: 'career',
          matchScore: 84,
          components: { radarMatch: 86, tagMatch: 82, rubricMatch: 84 },
          supportingDimensions: [
            { dimension: 'Desain Antarmuka', score: 86 },
            { dimension: 'Komunikasi', score: 82 },
          ],
          supportingTags: ['tag-design-01', 'tag-communication-05'],
          evidenceCount: 3,
          supportingPortfolios: [
            { portfolioId: 'p-3', title: 'Redesain Antarmuka Portal Sekolah' },
          ],
          suggestedPathways: [
            'Program Studi S1 Desain Komunikasi Visual',
            'UI/UX Designer, Design System Specialist, Visual Content Lead',
          ],
          rationale: 'Didukung oleh karya desain sistem berbasis riset pengguna serta kemampuan komunikasi visual.',
        },
      ],
      studyPaths: [
        {
          id: 'rec_sp_01',
          code: 'SP-SI',
          title: 'S1 Sistem Informasi / Teknik Informatika',
          cluster: 'Teknologi Informasi & Bisnis Terapan',
          description: 'Program studi perpaduan teknologi rekayasa komputasi dan strategi manajemen data bisnis.',
          type: 'study',
          matchScore: 90,
          components: { radarMatch: 92, tagMatch: 88, rubricMatch: 90 },
          supportingDimensions: [
            { dimension: 'Algoritma & Pemrograman', score: 92 },
            { dimension: 'Kolaborasi Tim', score: 88 },
          ],
          supportingTags: ['tag-web-02', 'tag-database-03'],
          evidenceCount: 5,
          supportingPortfolios: [
            { portfolioId: 'p-1', title: 'Sistem Monitoring Limbah IoT & Web' },
          ],
          suggestedPathways: ['S1 Sistem Informasi', 'S1 Teknik Informatika', 'D4 Rekayasa Perangkat Lunak'],
          rationale: 'Karakteristik proyek siswa sangat selaras dengan kurikulum analisis data dan rekayasa perangkat lunak.',
        },
      ],
      disclaimer: 'Rekomendasi bersifat panduan eksploratif berbasis karya nyata tervalidasi dan bukan prediksi masa depan mutlak.',
    };
  }

  public async getStudentRecommendations(forceRefresh = false): Promise<RecommendationResponse> {
    if (typeof window !== 'undefined' && !window.navigator.onLine) {
      return this.getCachedRecommendations();
    }
    try {
      const url = `${API_BASE}/api/v1/student/recommendations${forceRefresh ? '?force_refresh=true' : ''}`;
      const res = await fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
        },
        signal: AbortSignal.timeout(200),
      });

      if (res.ok) {
        return await res.json();
      }
    } catch {
      // Fallback to instant mock response
    }

    return this.getCachedRecommendations();
  }

  public async refreshStudentRecommendations(): Promise<RecommendationResponse> {
    const csrfToken = await ensureCsrfToken(API_BASE);
    const res = await fetch(`${API_BASE}/api/v1/student/recommendations/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
        ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
      },
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const msg = errorData.error?.message || errorData.detail?.message || `Gagal memperbarui rekomendasi (HTTP ${res.status})`;
      throw new Error(msg);
    }

    return await res.json();
  }

  public async generateProfessionalDescription(
    portfolioId: string,
    forceRegenerate = false
  ): Promise<ProfessionalDescriptionResponse> {
    const csrfToken = await ensureCsrfToken(API_BASE);
    const url = `${API_BASE}/api/v1/student/portfolio/${portfolioId}/professional-description${forceRegenerate ? '?force_regenerate=true' : ''}`;
    const res = await fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
        ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
      },
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const msg = errorData.error?.message || errorData.detail?.message || `Gagal membuat deskripsi profesional (HTTP ${res.status})`;
      throw new Error(msg);
    }

    return await res.json();
  }

  public async getProfessionalDescription(portfolioId: string): Promise<ProfessionalDescriptionResponse> {
    const res = await fetch(`${API_BASE}/api/v1/student/portfolio/${portfolioId}/professional-description`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const msg = errorData.error?.message || errorData.detail?.message || `Gagal mengambil deskripsi profesional (HTTP ${res.status})`;
      throw new Error(msg);
    }

    return await res.json();
  }
}

export const recommendationService: IRecommendationService = new HTTPRecommendationService();
