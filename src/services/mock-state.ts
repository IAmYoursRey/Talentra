import { PortfolioItem, PortfolioStatus, ValidationTimelineEvent } from '../types/portfolio.types';
import { UserProfile, UserRole } from '../types/auth.types';
import { INITIAL_MOCK_PORTFOLIO_ITEMS } from '../mocks/portfolio.mock';
import { MOCK_STUDENT, MOCK_TEACHER, MOCK_ADMIN, MOCK_ALL_USERS } from '../mocks/users.mock';
import { RubricAssessment } from '../types/review.types';

class MockAppState {
  private static instance: MockAppState;

  private currentUser: UserProfile = MOCK_STUDENT;
  private portfolioItems: PortfolioItem[] = [...INITIAL_MOCK_PORTFOLIO_ITEMS];
  private users: UserProfile[] = [...MOCK_ALL_USERS];
  private rubricAssessmentsMap: Map<string, RubricAssessment[]> = new Map();
  private listeners: Set<() => void> = new Set();

  private constructor() {
    if (typeof window !== 'undefined') {
      try {
        const storedPortfolios = localStorage.getItem('talentra_offline_portfolios');
        if (storedPortfolios) {
          const parsed = JSON.parse(storedPortfolios);
          if (Array.isArray(parsed) && parsed.length > 0) {
            this.portfolioItems = parsed;
          }
        }
        const storedRubrics = localStorage.getItem('talentra_offline_rubrics');
        if (storedRubrics) {
          const parsed = JSON.parse(storedRubrics);
          Object.entries(parsed).forEach(([k, v]) => {
            this.rubricAssessmentsMap.set(k, v as RubricAssessment[]);
          });
        }
      } catch {
        // Fallback to default mock items
      }
    }
  }

  public static getInstance(): MockAppState {
    if (!MockAppState.instance) {
      MockAppState.instance = new MockAppState();
    }
    return MockAppState.instance;
  }

  public subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify(): void {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('talentra_offline_portfolios', JSON.stringify(this.portfolioItems));
        const rubricObj: Record<string, RubricAssessment[]> = {};
        this.rubricAssessmentsMap.forEach((v, k) => {
          rubricObj[k] = v;
        });
        localStorage.setItem('talentra_offline_rubrics', JSON.stringify(rubricObj));
      } catch {
        // Ignore localStorage quota errors
      }
    }
    this.listeners.forEach((listener) => listener());
  }

  // --- Auth & Role Switching ---
  public getCurrentUser(): UserProfile {
    return { ...this.currentUser };
  }

  public setCurrentRole(role: UserRole): UserProfile {
    if (role === 'student') this.currentUser = { ...MOCK_STUDENT };
    else if (role === 'teacher') this.currentUser = { ...MOCK_TEACHER };
    else if (role === 'admin') this.currentUser = { ...MOCK_ADMIN };
    this.notify();
    return this.getCurrentUser();
  }

  public getAllUsers(): UserProfile[] {
    return [...this.users];
  }

  // --- Portfolio Operations ---
  public getPortfolioItems(): PortfolioItem[] {
    return [...this.portfolioItems];
  }

  public getPortfolioItemById(id: string): PortfolioItem | undefined {
    const item = this.portfolioItems.find((p) => p.id === id);
    return item ? { ...item } : undefined;
  }

  public addPortfolioItem(newItem: Omit<PortfolioItem, 'id' | 'timeline' | 'createdAt' | 'updatedAt'>): PortfolioItem {
    const id = `prt_${Date.now()}`;
    const timestamp = new Date().toISOString();
    const formattedTime = new Date().toLocaleString('id-ID', { dateStyle: 'short', timeStyle: 'short' });

    const timelineEvent: ValidationTimelineEvent = {
      id: `tl_${Date.now()}`,
      status: newItem.status,
      actorName: this.currentUser.name,
      actorRole: 'student',
      timestamp: formattedTime,
      note: newItem.status === 'draft' ? 'Draf portofolio disimpan' : 'Diajukan untuk validasi guru pembimbing',
    };

    const created: PortfolioItem = {
      ...newItem,
      id,
      timeline: [timelineEvent],
      createdAt: timestamp,
      updatedAt: timestamp,
    };

    this.portfolioItems.unshift(created);
    this.notify();
    return created;
  }

  public updatePortfolioStatus(
    id: string,
    newStatus: PortfolioStatus,
    note?: string,
    feedback?: string,
    rubric?: RubricAssessment[]
  ): PortfolioItem | null {
    const index = this.portfolioItems.findIndex((p) => p.id === id);
    if (index === -1) return null;

    const item = this.portfolioItems[index];
    const timestamp = new Date().toISOString();
    const formattedTime = new Date().toLocaleString('id-ID', { dateStyle: 'short', timeStyle: 'short' });

    const newTimelineEvent: ValidationTimelineEvent = {
      id: `tl_${Date.now()}`,
      status: newStatus,
      actorName: this.currentUser.name,
      actorRole: this.currentUser.role === 'student' ? 'student' : 'teacher',
      timestamp: formattedTime,
      note: note || `Status diperbarui menjadi ${newStatus}`,
    };

    const updatedItem: PortfolioItem = {
      ...item,
      status: newStatus,
      teacherFeedback: feedback !== undefined ? feedback : item.teacherFeedback,
      timeline: [...item.timeline, newTimelineEvent],
      updatedAt: timestamp,
    };

    this.portfolioItems[index] = updatedItem;

    if (rubric && rubric.length > 0) {
      this.rubricAssessmentsMap.set(id, rubric);
    }

    this.notify();
    return updatedItem;
  }

  public resubmitPortfolio(id: string, updatedFields: Partial<PortfolioItem>): PortfolioItem | null {
    const index = this.portfolioItems.findIndex((p) => p.id === id);
    if (index === -1) return null;

    const item = this.portfolioItems[index];
    const timestamp = new Date().toISOString();
    const formattedTime = new Date().toLocaleString('id-ID', { dateStyle: 'short', timeStyle: 'short' });

    const resubmitEvent: ValidationTimelineEvent = {
      id: `tl_${Date.now()}`,
      status: 'submitted',
      actorName: this.currentUser.name,
      actorRole: 'student',
      timestamp: formattedTime,
      note: 'Perbaikan portofolio diajukan ulang untuk validasi',
    };

    const updated: PortfolioItem = {
      ...item,
      ...updatedFields,
      status: 'submitted',
      timeline: [...item.timeline, resubmitEvent],
      updatedAt: timestamp,
    };

    this.portfolioItems[index] = updated;
    this.notify();
    return updated;
  }

  public getRubricForPortfolio(id: string): RubricAssessment[] | undefined {
    return this.rubricAssessmentsMap.get(id);
  }
}

export const mockAppState = MockAppState.getInstance();
