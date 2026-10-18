// Service worker : l'appli (HTML + données + carte) fonctionne hors ligne ; les tuiles de carte sont mises en cache au fil de la navigation.
// Les flux temps réel ne passent jamais par le cache.
const V = 'plan-azur-v4';
const SHELL = ['./', 'index.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'maskable-512.png', 'apple-touch-icon.png', 'favicon.ico', 'favicon-32.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(V).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V && k !== 'tiles-v1').map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const req = e.request; if (req.method !== 'GET') return;
  const u = new URL(req.url);
  if (/tile\.openstreetmap|cartocdn|openstreetmap\.fr/.test(u.host)) {
    e.respondWith(caches.open('tiles-v1').then(async c => {
      const hit = await c.match(req); if (hit) return hit;
      try { const r = await fetch(req); if (r.ok || r.type === 'opaque') { c.put(req, r.clone()); c.keys().then(k => { if (k.length > 1500) c.delete(k[0]); }); } return r; }
      catch (_) { return Response.error(); }
    }));
    return;
  }
  if (u.origin === location.origin) {
    e.respondWith(fetch(req).then(r => { const cp = r.clone(); caches.open(V).then(c => c.put(req, cp)); return r; }).catch(() => caches.match(req).then(r => r || caches.match('index.html'))));
  }
});
