// TALENTRA.ID PWA Service Worker (Phase 2 Auth-Safe Cache Policy)
const CACHE_NAME = 'talentra-static-v1';
const OFFLINE_URL = '/offline';

const STATIC_ASSETS = [
  '/offline',
  '/manifest.webmanifest',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // 1. NEVER cache authentication endpoints or any API requests
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  // 2. NEVER cache protected role routes (/student, /teacher, /admin)
  if (
    url.pathname.startsWith('/student') ||
    url.pathname.startsWith('/teacher') ||
    url.pathname.startsWith('/admin')
  ) {
    return;
  }

  // 3. For state-changing non-GET methods, never cache
  if (event.request.method !== 'GET') {
    return;
  }

  // 4. Stale-while-revalidate for static assets, network-first for pages
  if (
    url.pathname.startsWith('/_next/static/') ||
    url.pathname.startsWith('/icons/')
  ) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        return (
          cached ||
          fetch(event.request).then((response) => {
            if (response.status === 200) {
              const copy = response.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
            }
            return response;
          })
        );
      })
    );
  }
});
