import type { Metadata, Viewport } from 'next';
import { Suspense } from 'react';
import './globals.css';
import { TopProgressBar } from '../components/common/TopProgressBar';

export const metadata: Metadata = {
  title: 'TALENTRA.ID — Portofolio Digital Pintar Siswa',
  description:
    'Platform portofolio digital pintar dan analitik talenta siswa sekolah berbasis proof-of-work nyata, validasi guru, dan rekomendasi studi/karier objektif.',
  applicationName: 'TALENTRA.ID',
  keywords: ['portofolio digital', 'talenta siswa', 'proof of work', 'validasi guru', 'analitik talenta sekolah'],
  authors: [{ name: 'TALENTRA.ID' }],
  icons: {
    icon: '/icons/icon-192.svg',
    apple: '/icons/icon-192.svg',
  },
};

export const viewport: Viewport = {
  themeColor: '#3157D5',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
};

import { OfflineProvider } from '../context/OfflineContext';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-[#F8FAFC] font-sans antialiased text-slate-800">
        <OfflineProvider>
          <Suspense fallback={null}>
            <TopProgressBar />
          </Suspense>
          {children}
        </OfflineProvider>
      </body>
    </html>
  );
}
