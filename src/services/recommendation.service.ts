import {
  RecommendationResponse,
  ProfessionalDescriptionResponse,
} from '../types/recommendation.types';

export interface IRecommendationService {
  getStudentRecommendations(forceRefresh?: boolean): Promise<RecommendationResponse>;
  refreshStudentRecommendations(): Promise<RecommendationResponse>;
  generateProfessionalDescription(portfolioId: string, forceRegenerate?: boolean): Promise<ProfessionalDescriptionResponse>;
  getProfessionalDescription(portfolioId: string): Promise<ProfessionalDescriptionResponse>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class HTTPRecommendationService implements IRecommendationService {
  public async getStudentRecommendations(forceRefresh = false): Promise<RecommendationResponse> {
    const url = `${API_BASE}/api/v1/student/recommendations${forceRefresh ? '?force_refresh=true' : ''}`;
    const res = await fetch(url, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const msg = errorData.error?.message || errorData.detail?.message || `Gagal memuat rekomendasi (HTTP ${res.status})`;
      throw new Error(msg);
    }

    return await res.json();
  }

  public async refreshStudentRecommendations(): Promise<RecommendationResponse> {
    const res = await fetch(`${API_BASE}/api/v1/student/recommendations/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
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
    const url = `${API_BASE}/api/v1/student/portfolio/${portfolioId}/professional-description${forceRegenerate ? '?force_regenerate=true' : ''}`;
    const res = await fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
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
