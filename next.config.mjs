/** @type {import('next').NextConfig} */
const BACKEND_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000';

const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() {
    // Development-only proxy rewrite to local FastAPI server (:8000).
    // In production, Next.js performs NO rewrites; Vercel routes /api/v1/* directly to api/index.py preserving the full path.
    if (process.env.NODE_ENV === 'development') {
      const backendUrl = process.env.API_BASE_URL || 'http://127.0.0.1:8000';
      return [
        {
          source: '/api/v1/:path*',
          destination: `${backendUrl}/api/v1/:path*`,
        },
      ];
    }
    return [];
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
      {
        source: '/verify/:token*',
        headers: [
          {
            key: 'Referrer-Policy',
            value: 'no-referrer',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
