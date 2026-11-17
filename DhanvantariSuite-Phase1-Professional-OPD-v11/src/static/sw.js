const CACHE_NAME = 'dhanvantari-opd-shell-v1';
const SHELL_URLS = [
  '/ui/',
  '/ui/index.html',
  '/ui/manifest.json',
  '/ui/icon-192.png',
  '/ui/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_URLS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  // Always keep API calls network-only for live clinic sync
  if (event.request.method !== 'GET' || url.pathname.startsWith('/api/')) {
    return;
  }
  // Network-first with cache fallback for static app shell
  if (url.origin === self.location.origin && url.pathname.startsWith('/ui/')) {
    event.respondWith(
      fetch(event.request)
        .then((res) => {
          if (res && res.ok) {
            const copy = res.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return res;
        })
        .catch(() => caches.match(event.request))
    );
  }
});
