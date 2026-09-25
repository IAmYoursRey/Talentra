import { SkillRadarPoint, SkillSnapshot, SkillDetail, SkillContributor } from '../types/skill.types';
import { mockAppState } from './mock-state';

export interface ISkillService {
  getStudentSkillSnapshot(studentId?: string): Promise<SkillSnapshot>;
  getSkillDetail(skillName: string, studentId?: string): Promise<SkillDetail | null>;
  subscribeSkills(callback: () => void): () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class HTTPSkillService implements ISkillService {
  private subscribers: Array<() => void> = [];

  public subscribeSkills(callback: () => void): () => void {
    this.subscribers.push(callback);
    return () => {
      this.subscribers = this.subscribers.filter((s) => s !== callback);
    };
  }

  public async getStudentSkillSnapshot(studentId?: string): Promise<SkillSnapshot> {
    try {
      const res = await fetch(`${API_BASE}/api/v1/student/skills`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (res.ok) {
        const json = await res.json();
        const rawRadar = json.radar || [];
        const rawRubrics = json.teacherRubrics || [];

        const radarPoints: SkillRadarPoint[] = rawRadar.map((r: any) => ({
          skill: r.displayName || r.dimension,
          dimensionCode: r.dimension,
          score: r.score,
          fullMark: r.fullMark || 100,
          approvedEvidenceCount: r.evidenceCount || 0,
        }));

        const sortedSkills = [...radarPoints]
          .filter((p) => p.score > 0)
          .sort((a, b) => b.score - a.score);

        const topSkills = sortedSkills.slice(0, 3).map((s) => ({
          name: s.skill,
          score: s.score,
          level: s.score >= 80 ? 'Tingkat Mahir' : s.score >= 60 ? 'Tingkat Menengah' : 'Tingkat Dasar',
        }));

        return {
          scoringVersion: json.scoringVersion || 'approved-evidence-count-v1',
          radarPoints,
          topSkills: topSkills.length > 0 ? topSkills : [{ name: 'Belum Ada Bukti Disetujui', score: 0, level: 'Menunggu Validasi' }],
          totalApprovedEvidence: json.approvedEvidenceCount || 0,
          lastCalculatedAt: new Date().toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' }),
          teacherRubrics: rawRubrics,
        };
      }
    } catch {
      // Backend unreachable; gracefully fallback to mock
    }

    // Mock fallback
    const targetStudentId = studentId || mockAppState.getCurrentUser().id;
    const approvedItems = mockAppState
      .getPortfolioItems()
      .filter((p) => p.studentId === targetStudentId && p.status === 'approved');

    const tagCount: Record<string, number> = {};
    approvedItems.forEach((item) => {
      item.tags.forEach((tag) => {
        tagCount[tag] = (tagCount[tag] || 0) + 1;
      });
    });

    const radarDimensions = [
      { key: 'Komunikasi', code: 'communication', tag: 'public-speaking' },
      { key: 'Kepemimpinan', code: 'leadership', tag: 'leadership' },
      { key: 'Literasi Digital', code: 'digital-literacy', tag: 'web-development' },
      { key: 'Pemecahan Masalah', code: 'problem-solving', tag: 'problem-solving' },
      { key: 'Kreativitas & Inovasi', code: 'creativity', tag: 'ui-ux' },
      { key: 'Kolaborasi Tim', code: 'collaboration', tag: 'teamwork' },
    ];

    const radarPoints: SkillRadarPoint[] = radarDimensions.map((dim) => {
      const count = tagCount[dim.tag] || 0;
      const score = Math.min(100, count * 20);
      return {
        skill: dim.key,
        dimensionCode: dim.code,
        score,
        fullMark: 100,
        approvedEvidenceCount: count,
      };
    });

    const sortedSkills = [...radarPoints]
      .filter((p) => p.score > 0)
      .sort((a, b) => b.score - a.score);

    const topSkills = sortedSkills.slice(0, 3).map((s) => ({
      name: s.skill,
      score: s.score,
      level: s.score >= 80 ? 'Tingkat Mahir' : s.score >= 60 ? 'Tingkat Menengah' : 'Tingkat Dasar',
    }));

    return {
      scoringVersion: 'approved-evidence-count-v1',
      radarPoints,
      topSkills: topSkills.length > 0 ? topSkills : [{ name: 'Belum Ada Bukti Disetujui', score: 0, level: 'Menunggu Validasi' }],
      totalApprovedEvidence: approvedItems.length,
      lastCalculatedAt: new Date().toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' }),
      teacherRubrics: [
        { dimensionCode: 'initiative', displayName: 'Inisiatif', averageScore: 4.0, assessmentCount: approvedItems.length },
        { dimensionCode: 'collaboration', displayName: 'Kolaborasi', averageScore: 4.2, assessmentCount: approvedItems.length },
        { dimensionCode: 'communication', displayName: 'Komunikasi', averageScore: 3.8, assessmentCount: approvedItems.length },
        { dimensionCode: 'responsibility', displayName: 'Tanggung Jawab', averageScore: 4.5, assessmentCount: approvedItems.length },
        { dimensionCode: 'resilience', displayName: 'Daya Juang', averageScore: 3.5, assessmentCount: approvedItems.length },
      ],
    };
  }

  public async getSkillDetail(skillName: string, studentId?: string): Promise<SkillDetail | null> {
    try {
      const res = await fetch(`${API_BASE}/api/v1/student/skills`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (res.ok) {
        const json = await res.json();
        const rawRadar = json.radar || [];
        const match = rawRadar.find(
          (r: any) =>
            r.displayName?.toLowerCase() === skillName.toLowerCase() ||
            r.dimension?.toLowerCase() === skillName.toLowerCase()
        );

        if (match) {
          const contributors: SkillContributor[] = (match.contributors || []).map((c: any) => ({
            portfolioId: c.portfolioId,
            portfolioTitle: c.title,
            date: c.approvedAt ? c.approvedAt.split('T')[0] : new Date().toISOString().split('T')[0],
            contributionScore: 20,
            activityType: 'project',
            tags: c.tags || [],
          }));

          return {
            skillName: match.displayName || match.dimension,
            score: match.score,
            category: 'Kompetensi Tervalidasi',
            approvedEvidenceCount: match.evidenceCount,
            contributors,
            rubricNotes: [
              'Dihitung secara deterministik hanya dari karya yang telah disetujui guru (min 100, bukti x 20)',
              'Didukung rubrik observasi soft-skill 1–5 oleh guru pembimbing',
            ],
          };
        }
      }
    } catch {
      // Backend unreachable; fallback to mock
    }

    // Mock fallback
    const targetStudentId = studentId || mockAppState.getCurrentUser().id;
    const approvedItems = mockAppState
      .getPortfolioItems()
      .filter((p) => p.studentId === targetStudentId && p.status === 'approved');

    const contributors = approvedItems.map((item) => ({
      portfolioId: item.id,
      portfolioTitle: item.title,
      date: item.date,
      contributionScore: 20,
      activityType: item.activityType,
      tags: item.tags,
    }));

    return {
      skillName,
      score: Math.min(100, contributors.length * 20),
      category: 'Kompetensi Tervalidasi',
      approvedEvidenceCount: contributors.length,
      contributors,
      rubricNotes: [
        'Dihitung secara deterministik hanya dari karya yang telah disetujui guru',
        'Didukung rubrik observasi soft-skill 1–5 oleh guru pembimbing',
      ],
    };
  }
}

export const skillService: ISkillService = new HTTPSkillService();
