# Plan du réseau Lignes d'Azur — mode d'emploi

## Mettre en ligne (GitHub Pages)
Déposer **tout le contenu de ce dossier à la racine** du dépôt (index.html, manifest.webmanifest, sw.js, favicon.ico, favicon-32.png, icon-192.png, icon-512.png, maskable-512.png, apple-touch-icon.png). Activer Pages (Settings → Pages → branche main, dossier /root).
L'installation en application (bouton « 📲 Installer ») ne fonctionne qu'en **https**, donc sur Pages, pas en ouvrant le fichier directement.

## Icônes
- `favicon.ico`, `favicon-32.png` : onglet du navigateur (coins arrondis).
- `icon-192.png`, `icon-512.png` : icône de l'appli (coins arrondis, fond transparent).
- `maskable-512.png` : icône Android « adaptative » (plein cadre, l'OS applique sa forme).
- `apple-touch-icon.png` : iPhone / iPad (carré, iOS arrondit lui-même).

## Temps réel
Flux officiels (GTFS-RT, licence ouverte) :
- `https://ara-api.enroute.mobi/rla/gtfs/trip-updates`
- `https://ara-api.enroute.mobi/rla/gtfs/vehicle-positions`
Le bouton « Temps réel » (en-tête) affiche l'état. Si le navigateur bloque l'accès (CORS), déployer `rt-proxy/worker.js` sur Cloudflare Workers (gratuit), puis ⚙ → Proxy = `https://TON-WORKER.workers.dev/?url=`.
Les retards s'affichent sur les prochains départs (point vert), les positions des bus sur la carte, et sur les trajets calculés pour aujourd'hui.

## Mettre à jour les horaires (nouveau GTFS)
1. Télécharger le GTFS : https://chouette.enroute.mobi/api/v1/datas/OpendataRLA/gtfs.zip et le décompresser.
2. `cd outils && pip install pandas && python3 build_data.py <dossier_gtfs> data.json && python3 assemble.py`
3. Remplacer `index.html` du dépôt par celui produit, et incrémenter `V` dans `sw.js` (ex. plan-azur-v5) pour forcer la mise à jour de l'appli installée.

Données : Métropole Nice Côte d'Azur / Lignes d'Azur (Licence Ouverte 2.0). Site non officiel.
