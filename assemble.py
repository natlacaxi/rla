"""Régénère index.html à partir d'un nouveau GTFS.
   python3 build_data.py <dossier_gtfs_decompresse> data.json   (nécessite pandas)
   python3 assemble.py                                          (produit ../index.html)"""
import os
d = os.path.dirname(os.path.abspath(__file__))
r = lambda f: open(os.path.join(d, f), encoding='utf-8').read()
h = r('template.html').replace('__LEAFLET_CSS__', r('leaflet.css')).replace('__LEAFLET_JS__', r('leaflet.js'))
h = h.replace('__FAV__', r('fav32.txt')).replace('__LOGO__', r('logo.txt')).replace('__DATA__', r('data.json'))
open(os.path.join(d, '..', 'index.html'), 'w', encoding='utf-8').write(h)
print('index.html régénéré')
