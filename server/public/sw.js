const CACHE_NAME = "seccam-v4";
const MAX_ASTRO_ENTRIES = 80;

const PRECACHE = [
  "/",
  "/archive",
  "/settings",
  "/logs",
  "/manifest.json",
  "/icon.png",
];

/** Cache a response clone for the given request */
async function cacheResponse(request, response) {
  const cache = await caches.open(CACHE_NAME);
  await cache.put(request, response.clone());
}

/** Trim old /_astro/ entries to prevent unbounded cache growth */
let trimming = false;
async function trimAstroCache() {
  if (trimming) return;
  trimming = true;
  try {
    const cache = await caches.open(CACHE_NAME);
    const keys = await cache.keys();
    const astroKeys = keys.filter((r) =>
      new URL(r.url).pathname.startsWith("/_astro/")
    );

    if (astroKeys.length <= MAX_ASTRO_ENTRIES) return;

    // Sort by Date header so we evict the oldest entries first
    const entries = await Promise.all(
      astroKeys.map(async (request) => {
        let time = 0;
        try {
          const res = await cache.match(request);
          if (res) {
            const header = res.headers.get("Date") || res.headers.get("Last-Modified");
            if (header) {
              const parsed = Date.parse(header);
              if (!Number.isNaN(parsed)) time = parsed;
            }
          }
        } catch {}
        return { request, time };
      })
    );

    entries.sort((a, b) => a.time - b.time);
    const excess = entries.slice(0, entries.length - MAX_ASTRO_ENTRIES);
    await Promise.all(excess.map(({ request }) => cache.delete(request)));
  } finally {
    trimming = false;
  }
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      Promise.allSettled(
        PRECACHE.map((url) =>
          fetch(url)
            .then((res) => {
              if (res.ok) return cache.put(url, res);
              console.warn(`[SW] precache failed for ${url}: ${res.status}`);
            })
            .catch((err) => console.warn(`[SW] precache error for ${url}:`, err))
        )
      )
    )
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    Promise.all([
      // Clean old caches
      caches.keys().then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key))
        )
      ),
      // Enable navigation preload if supported
      self.registration.navigationPreload?.enable(),
    ])
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Don't cache MediaMTX (WebRTC/HLS) or Flask API calls
  if (url.port === "8889" || url.port === "8888" || url.port === "5005") {
    return;
  }

  // Only handle same-origin requests
  if (url.origin !== self.location.origin) {
    return;
  }

  // Astro static assets (/_astro/) are content-hashed — cache-first since
  // the filename changes on every build, so stale entries are never served.
  if (url.pathname.startsWith("/_astro/")) {
    event.respondWith(
      (async () => {
        const cached = await caches.match(request);
        if (cached) return cached;
        const response = await fetch(request);
        if (response.ok) {
          await cacheResponse(request, response);
          await trimAstroCache();
        }
        return response;
      })()
    );
    return;
  }

  // Navigation requests: use preloaded response when available
  if (request.mode === "navigate") {
    event.respondWith(
      (async () => {
        try {
          // Use navigation preload response if available
          const preloadResponse = await event.preloadResponse;
          if (preloadResponse) {
            await cacheResponse(request, preloadResponse);
            return preloadResponse;
          }

          const response = await fetch(request);
          if (response.ok) await cacheResponse(request, response);
          return response;
        } catch {
          const cached = await caches.match(request);
          return cached || (await caches.match("/")) || new Response("Offline", { status: 503 });
        }
      })()
    );
    return;
  }

  // Everything else: network-first with cache fallback
  event.respondWith(
    (async () => {
      try {
        const response = await fetch(request);
        if (response.ok) await cacheResponse(request, response);
        return response;
      } catch {
        const cached = await caches.match(request);
        return cached || new Response("Offline", { status: 503 });
      }
    })()
  );
});
