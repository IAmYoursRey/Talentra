import { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'TALENTRA.ID — Portofolio Digital Pintar Siswa',
    short_name: 'TALENTRA.ID',
    description: 'Platform portofolio digital pintar dan analitik talenta siswa sekolah berbasis proof-of-work terverifikasi.',
    start_url: '/',
    display: 'standalone',
    background_color: '#F8FAFC',
    theme_color: '#3157D5',
    orientation: 'portrait-primary',
    icons: [
      {
        src: '/icons/icon-192.svg',
        sizes: '192x192',
        type: 'image/svg+xml',
      },
      {
        src: '/icons/icon-512.svg',
        sizes: '512x512',
        type: 'image/svg+xml',
      },
    ],
  };
}
