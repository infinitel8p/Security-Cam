const CACHE_NAME = "seccam-v1";

const SHELL_ASSETS = [
  "/",
  "/archive",
  "/settings",
  "/manifest.json",
  "/icon.png",
  "/fonts/inter-latin.woff2",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Dont cache MediaMTX WebRTC traffic (port 8889) or Flask API calls (port 5005)
  if (url.port === "8889" || url.port === "5005") {
    return; // network only, no interception
  }

  if (request.mode === "navigate" || url.origin === self.location.origin) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() => caches.match(request))
    );
    return;
  }
});
