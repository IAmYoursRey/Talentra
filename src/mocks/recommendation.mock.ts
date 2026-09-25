import { CareerStudyRecommendation } from '../types/recommendation.types';

export const MOCK_RECOMMENDATIONS: CareerStudyRecommendation[] = [
  {
    id: 'rec_001',
    title: 'Sistem Informasi & Rekayasa Produk Digital',
    category: 'study',
    fieldCluster: 'Teknologi Informasi & Bisnis Terapan',
    matchPercentage: 92,
    supportingSkills: [
      { name: 'Web Development', relevanceScore: 94 },
      { name: 'Problem Solving', relevanceScore: 88 },
      { name: 'UI/UX Design', relevanceScore: 85 },
      { name: 'Leadership', relevanceScore: 78 },
    ],
    evidenceCount: 2,
    evidenceTitles: [
      'Aplikasi Monitoring Sampah Sekolah Berbasis IoT & Dashboard Web',
      'Redesain Antarmuka & UX Portal OSIS SMA Negeri 1 Teladan',
    ],
    rationale: 'Berdasarkan karya tervalidasi yang menunjukkan konsistensi tinggi pada pengembangan aplikasi web, perancangan antarmuka, dan penyelesaian masalah operasional nyata di lingkungan sekolah.',
    suggestedPathways: [
      'Program Studi S1 Sistem Informasi / Information Systems',
      'Program Studi D4/S1 Terapan Rekayasa Perangkat Lunak Aplikasi',
      'Jalur Karir: Product Specialist, Associate Product Manager, Fullstack Developer',
    ],
    isDemoData: true,
  },
  {
    id: 'rec_002',
    title: 'Desain Komunikasi Visual & Interaksi Pengguna (UI/UX)',
    category: 'career',
    fieldCluster: 'Industri Kreatif & Digital Media',
    matchPercentage: 86,
    supportingSkills: [
      { name: 'UI/UX Design', relevanceScore: 90 },
      { name: 'Graphic Design', relevanceScore: 82 },
      { name: 'Teamwork', relevanceScore: 85 },
      { name: 'Public Speaking', relevanceScore: 75 },
    ],
    evidenceCount: 2,
    evidenceTitles: [
      'Redesain Antarmuka & UX Portal OSIS SMA Negeri 1 Teladan',
      'Juara 1 Lomba Debat Bahasa Indonesia Tingkat Pelajar Provinsi',
    ],
    rationale: 'Didukung oleh bukti karya desain sistem berbasis riset pengguna serta kemampuan komunikasi dan artikulasi gagasan yang terbukti dalam kompetensi terverifikasi.',
    suggestedPathways: [
      'Program Studi S1 Desain Komunikasi Visual (DKV)',
      'Program Studi S1 Desain Interaksi & Media Digital',
      'Jalur Karir: UI/UX Designer, Design System Specialist, Visual Content Lead',
    ],
    isDemoData: true,
  },
  {
    id: 'rec_003',
    title: 'Manajemen Bisnis Digital & Transformasi Teknologi',
    category: 'study',
    fieldCluster: 'Manajemen & Kewirausahaan Modern',
    matchPercentage: 79,
    supportingSkills: [
      { name: 'Leadership', relevanceScore: 82 },
      { name: 'Public Speaking', relevanceScore: 80 },
      { name: 'Problem Solving', relevanceScore: 78 },
      { name: 'Communication', relevanceScore: 84 },
    ],
    evidenceCount: 2,
    evidenceTitles: [
      'Aplikasi Monitoring Sampah Sekolah Berbasis IoT & Dashboard Web',
      'Juara 1 Lomba Debat Bahasa Indonesia Tingkat Pelajar Provinsi',
    ],
    rationale: 'Menunjukkan perpaduan talenta teknis dasar dengan kecakapan kepemimpinan tim dan komunikasi publik yang persuasif.',
    suggestedPathways: [
      'Program Studi S1 Bisnis Digital / Digital Business',
      'Program Studi S1 Manajemen Teknologi',
      'Jalur Karir: Technology Consultant, Operations Lead, Startup Founder',
    ],
    isDemoData: true,
  },
];
