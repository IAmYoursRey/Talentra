import { SoftSkillRubricDimension } from '../types/review.types';

export const RUBRIC_LEVEL_LABELS: Record<1 | 2 | 3 | 4 | 5, string> = {
  1: 'Belum terlihat',
  2: 'Mulai terlihat',
  3: 'Cukup konsisten',
  4: 'Kuat',
  5: 'Sangat menonjol',
};

export const MOCK_RUBRIC_DIMENSIONS: SoftSkillRubricDimension[] = [
  {
    id: 'initiative',
    name: 'Inisiatif (Initiative)',
    description: 'Kemampuan mengambil tindakan proaktif tanpa menunggu arahan eksplisit.',
    levels: {
      1: 'Belum terlihat — Masih memerlukan instruksi langkah demi langkah',
      2: 'Mulai terlihat — Menunjukkan minat namun belum konsisten mandiri',
      3: 'Cukup konsisten — Mampu mencari solusi mandiri pada tugas umum',
      4: 'Kuat — Proaktif menawarkan gagasan dan menyelesaikan kendala',
      5: 'Sangat menonjol — Menginisiasi proyek dan menggerakkan lingkungan sekitar',
    },
  },
  {
    id: 'collaboration',
    name: 'Kolaborasi (Collaboration)',
    description: 'Kemampuan bekerja sama, menghargai perspektif rekan, dan mencapai tujuan bersama.',
    levels: {
      1: 'Belum terlihat — Cenderung bekerja terisolasi atau sulit beradaptasi',
      2: 'Mulai terlihat — Menerima tugas kelompok tetapi keterlibatan minim',
      3: 'Cukup konsisten — Berkontribusi aktif dan berkomunikasi baik dengan rekan',
      4: 'Kuat — Memfasilitasi kerja tim dan saling mendukung saat ada kendala',
      5: 'Sangat menonjol — Menjadi perekat tim dan mampu mengatasi konflik secara bijak',
    },
  },
  {
    id: 'communication',
    name: 'Komunikasi (Communication)',
    description: 'Kejelasan penyampaian ide, kemampuan mendengar aktif, dan artikulasi ide karya.',
    levels: {
      1: 'Belum terlihat — Kesulitan mengartikulasikan tujuan karya',
      2: 'Mulai terlihat — Mampu menyampaikan poin dasar dengan bimbingan',
      3: 'Cukup konsisten — Presentasi runtut, terstruktur, dan mudah dipahami',
      4: 'Kuat — Menjelaskan konsep kompleks dengan bahasa persuasif dan lugas',
      5: 'Sangat menonjol — Komunikasi inspiratif, adaptif terhadap audiens yang beragam',
    },
  },
  {
    id: 'responsibility',
    name: 'Tanggung Jawab (Responsibility)',
    description: 'Akuntabilitas terhadap tenggat waktu, kualitas keluaran karya, dan etika berkarya.',
    levels: {
      1: 'Belum terlihat — Sering terlambat atau tidak menyelesaikan komitmen',
      2: 'Mulai terlihat — Menyelesaikan tugas jika diingatkan berulang kali',
      3: 'Cukup konsisten — Memenuhi tenggat waktu dan menjaga kualitas dasar',
      4: 'Kuat — Bertanggung jawab penuh atas hasil kerja dan beretika tinggi',
      5: 'Sangat menonjol — Standar mutu tinggi, dapat diandalkan secara konsisten',
    },
  },
  {
    id: 'resilience',
    name: 'Daya Juang & Adaptasi (Resilience)',
    description: 'Ketahanan menghadapi umpan balik revisi dan ketekunan menyelesaikan tantangan.',
    levels: {
      1: 'Belum terlihat — Mudah menyerah atau resisten terhadap masukan revisi',
      2: 'Mulai terlihat — Menerima revisi namun butuh motivasi eksternal',
      3: 'Cukup konsisten — Menindaklanjuti catatan perbaikan dengan tertib',
      4: 'Kuat — Memandang masukan sebagai peluang perbaikan dan lekas beradaptasi',
      5: 'Sangat menonjol — Sangat tangguh dalam iterasi dan terus menaikkan standar karya',
    },
  },
];
