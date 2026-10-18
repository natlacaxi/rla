// Proxy CORS minimal pour les flux GTFS-RT de Lignes d'Azur (Cloudflare Workers, plan gratuit suffisant).
// Déploiement : Cloudflare > Workers > Créer > coller ce fichier > Déployer.
// Dans le site : ⚙ (Temps réel) > Proxy = https://TON-WORKER.workers.dev/?url=
const ALLOW = [
  'https://ara-api.enroute.mobi/rla/gtfs/trip-updates',
  'https://ara-api.enroute.mobi/rla/gtfs/vehicle-positions',
];
const CORS = { 'access-control-allow-origin': '*', 'access-control-allow-methods': 'GET,OPTIONS', 'access-control-allow-headers': '*' };
export default {
  async fetch(req) {
    if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
    const target = new URL(req.url).searchParams.get('url');
    if (!ALLOW.includes(target)) return new Response('forbidden', { status: 403, headers: CORS });
    const r = await fetch(target, { cf: { cacheTtl: 15, cacheEverything: true } });
    return new Response(r.body, { status: r.status, headers: { ...CORS, 'content-type': 'application/x-protobuf', 'cache-control': 'public, max-age=15' } });
  },
};
