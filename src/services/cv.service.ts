import {
  CVBuilderContext,
  CVGenerateRequest,
  CVGenerateResponse,
  CVDetailSnapshot,
} from '../types/cv.types';

import { ensureCsrfToken } from '../lib/csrf';

export interface ICVService {
  getCVBuilderContext(): Promise<CVBuilderContext>;
  generateCV(req: CVGenerateRequest): Promise<CVGenerateResponse>;
  getCVDetail(snapshotId: string): Promise<CVDetailSnapshot>;
  downloadCVPdf(snapshotId: string): Promise<{ blob: Blob; filename: string }>;
  revokeCV(snapshotId: string, reason?: string): Promise<{ status: string; snapshotId: string }>;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window === 'undefined' ? (process.env.API_BASE_URL || 'http://127.0.0.1:8000') : '');

export class HTTPCVService implements ICVService {
  public async getCVBuilderContext(): Promise<CVBuilderContext> {
    const res = await fetch(`${API_BASE}/api/v1/student/cv`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const msg = errorData.error?.message || errorData.detail || `Gagal memuat konteks CV (HTTP ${res.status})`;
      throw new Error(msg);
    }

    return await res.json();
  }

  public async generateCV(req: CVGenerateRequest): Promise<CVGenerateResponse> {
    const csrfToken = await ensureCsrfToken(API_BASE);
    const res = await fetch(`${API_BASE}/api/v1/student/cv`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
      },
      body: JSON.stringify(req),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const msg = errorData.error?.message || errorData.detail || `Gagal menerbitkan CV (HTTP ${res.status})`;
      throw new Error(msg);
    }

    return await res.json();
  }

  public async getCVDetail(snapshotId: string): Promise<CVDetailSnapshot> {
    const res = await fetch(`${API_BASE}/api/v1/student/cv/${snapshotId}`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const msg = errorData.error?.message || errorData.detail || `Gagal memuat detail CV (HTTP ${res.status})`;
      throw new Error(msg);
    }

    return await res.json();
  }

  public async downloadCVPdf(snapshotId: string): Promise<{ blob: Blob; filename: string }> {
    const res = await fetch(`${API_BASE}/api/v1/student/cv/${snapshotId}/download`, {
      method: 'GET',
      credentials: 'include',
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const msg = errorData.error?.message || errorData.detail || `Gagal mengunduh dokumen PDF (HTTP ${res.status})`;
      throw new Error(msg);
    }

    const disposition = res.headers.get('Content-Disposition') || '';
    let filename = `TALENTRA-CV-${snapshotId}.pdf`;
    const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
    if (filenameMatch && filenameMatch[1]) {
      filename = filenameMatch[1];
    }

    const blob = await res.blob();
    return { blob, filename };
  }

  public async revokeCV(snapshotId: string, reason = 'Dicabut oleh siswa'): Promise<{ status: string; snapshotId: string }> {
    const csrfToken = await ensureCsrfToken(API_BASE);
    const res = await fetch(`${API_BASE}/api/v1/student/cv/${snapshotId}/revoke`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
      },
      body: JSON.stringify({ reason }),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const msg = errorData.error?.message || errorData.detail || `Gagal mencabut CV (HTTP ${res.status})`;
      throw new Error(msg);
    }

    return await res.json();
  }
}

export const cvService: ICVService = new HTTPCVService();
