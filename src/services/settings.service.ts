export interface SchoolIdentitySettings {
  schoolName: string;
  npsn: string;
  academicYear: string;
  semester: string;
  principalName: string;
  province: string;
}

export interface SecuritySettings {
  demoLogin: boolean;
  secureCookie: string;
  rbacMode: string;
  sessionTimeoutHours: number;
}

export interface StorageSettings {
  freeTier: string;
  privateFiles: string;
  maxFileSizeMb: number;
  softLimitThreshold: string;
  allowedFormats: string[];
}

export interface CVPolicySettings {
  evidenceMax: number;
  qrVerification: string;
  revocationMode: string;
  requireTeacherApproval: boolean;
}

export interface AllSchoolSettings {
  identity: SchoolIdentitySettings;
  security: SecuritySettings;
  storage: StorageSettings;
  cvPolicy: CVPolicySettings;
  updatedAt: string;
}

export const DEFAULT_SCHOOL_SETTINGS: AllSchoolSettings = {
  identity: {
    schoolName: 'SMAN 1 Ngoro',
    npsn: '20503021',
    academicYear: '2026 / 2027',
    semester: 'Semester 1 (Ganjil)',
    principalName: 'Dra. Hj. Siti Fatimah, M.Pd',
    province: 'Jawa Timur',
  },
  security: {
    demoLogin: true,
    secureCookie: 'ON',
    rbacMode: 'STRICT',
    sessionTimeoutHours: 24,
  },
  storage: {
    freeTier: 'ON',
    privateFiles: 'ON',
    maxFileSizeMb: 25,
    softLimitThreshold: '80%',
    allowedFormats: ['PDF', 'PNG', 'JPG', 'MP4', 'ZIP'],
  },
  cvPolicy: {
    evidenceMax: 8,
    qrVerification: 'ON',
    revocationMode: 'Immediate',
    requireTeacherApproval: true,
  },
  updatedAt: '2026-09-25T00:00:00Z',
};

class SettingsService {
  private cache: AllSchoolSettings = { ...DEFAULT_SCHOOL_SETTINGS };
  private isLoaded = false;

  constructor() {
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem('talentra_school_settings');
        if (stored) {
          this.cache = { ...DEFAULT_SCHOOL_SETTINGS, ...JSON.parse(stored) };
          this.isLoaded = true;
        }
      } catch {
        // Fallback
      }
    }
  }

  public getCachedSettings(): AllSchoolSettings {
    if (typeof window !== 'undefined' && !this.isLoaded) {
      try {
        const stored = localStorage.getItem('talentra_school_settings');
        if (stored) {
          this.cache = { ...DEFAULT_SCHOOL_SETTINGS, ...JSON.parse(stored) };
          this.isLoaded = true;
        }
      } catch {
        // Fallback
      }
    }
    return this.cache;
  }

  public async getSettings(): Promise<AllSchoolSettings> {
    return this.getCachedSettings();
  }

  public async updateSettings(partial: Partial<AllSchoolSettings>): Promise<AllSchoolSettings> {
    this.cache = {
      ...this.cache,
      ...partial,
      updatedAt: new Date().toISOString(),
    };

    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('talentra_school_settings', JSON.stringify(this.cache));
      } catch {
        // Fallback
      }
    }

    return this.cache;
  }

  public async resetToDefault(): Promise<AllSchoolSettings> {
    this.cache = { ...DEFAULT_SCHOOL_SETTINGS, updatedAt: new Date().toISOString() };
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('talentra_school_settings');
      } catch {
        // Fallback
      }
    }
    return this.cache;
  }
}

export const settingsService = new SettingsService();
