const CACHE_NAME = "seccam-v5";
const MAX_ASTRO_ENTRIES = 80;

const PRECACHE = [
  "/",
  "/archive",
  "/settings",
  "/logs",
  "/manifest.json",
  "/icon.png",
  "/icon-192.png",
];

/** Cache a response clone for the given request */
async function cacheResponse(request, response) {
  const cache = await caches.open(CACHE_NAME);
  await cache.put(request, response.clone());
}

/** Try to find a cached response, attempting multiple matching strategies */
async function matchCache(request) {
  const cache = await caches.open(CACHE_NAME);

  // 1. Exact match
  const exact = await cache.match(request);
  if (exact) return exact;

  // 2. Ignore query params (Safari sometimes appends tracking params)
  const noSearch = await cache.match(request, { ignoreSearch: true });
  if (noSearch) return noSearch;

  // 3. Try with/without trailing slash
  const url = new URL(request.url);
  const alt = url.pathname.endsWith("/")
    ? url.pathname.slice(0, -1)
    : url.pathname + "/";
  const altMatch = await cache.match(new Request(url.origin + alt));
  if (altMatch) return altMatch;

  return null;
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

    const entries = await Promise.all(
      astroKeys.map(async (request) => {
        let time = 0;
        try {
          const res = await cache.match(request);
          if (res) {
            const header =
              res.headers.get("Date") || res.headers.get("Last-Modified");
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
              console.warn(`[SW] precache skip ${url}: ${res.status}`);
            })
            .catch((err) => console.warn(`[SW] precache error ${url}:`, err))
        )
      )
    )
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    Promise.all([
      caches.keys().then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key))
        )
      ),
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

  // Astro static assets: content-hashed, cache-first
  if (url.pathname.startsWith("/_astro/")) {
    event.respondWith(
      (async () => {
        try {
          const cached = await caches.match(request);
          if (cached) return cached;
          const response = await fetch(request);
          if (response.ok) {
            await cacheResponse(request, response);
            await trimAstroCache();
          }
          return response;
        } catch {
          const cached = await caches.match(request);
          return cached || new Response("", { status: 503 });
        }
      })()
    );
    return;
  }

  // Navigation requests (HTML pages)
  if (request.mode === "navigate") {
    event.respondWith(
      (async () => {
        try {
          const preloadResponse = await event.preloadResponse;
          if (preloadResponse) {
            await cacheResponse(request, preloadResponse);
            return preloadResponse;
          }

          const response = await fetch(request);
          if (response.ok) await cacheResponse(request, response);
          return response;
        } catch {
          // Server unreachable - serve from cache
          const cached = await matchCache(request);
          if (cached) return cached;

          // Last resort: serve the cached root page (SPA shell)
          const root = await caches.match("/");
          return root || new Response("Offline", {
            status: 503,
            headers: { "Content-Type": "text/html" },
          });
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
        const cached = await matchCache(request);
        return cached || new Response("", { status: 503 });
      }
    })()
  );
});
