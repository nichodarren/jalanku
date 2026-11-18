// Service worker: cache kerangka aplikasi (bukan data API). Pemilik: M1.
// Naikkan VERSI setiap kali daftar berkas inti berubah.
const VERSI = "jalanku-v0.1.0";
const INTI = ["/", "/index.html", "/app.js", "/shared/gaya.css", "/shared/api.js", "/shared/ui.js",
  "/vendor/leaflet/leaflet.js", "/vendor/leaflet/leaflet.css"];

self.addEventListener("install", (e) => e.waitUntil(caches.open(VERSI).then((c) => c.addAll(INTI))));
self.addEventListener("activate", (e) =>
  e.waitUntil(caches.keys().then((k) => Promise.all(k.filter((n) => n !== VERSI).map((n) => caches.delete(n))))),
);
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin || url.pathname.startsWith("/api/")) return;
  // Jaringan dulu, cache bila offline: kode terbaru selalu dipakai saat online.
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
