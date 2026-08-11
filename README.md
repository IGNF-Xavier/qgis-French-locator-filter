# French Locator Filter - Un plugin de géocodage pour QGIS - version test


## Fonctionnalités

Le plugin ajoute un filtre dans la barre de recherche universelle (Localisateur) de QGIS, un outil de géocodage inversé, et des traitements Processing en lot, pour quatre sources de géocodage :

| Source                              | Préfixe locator | Géocodage direct | Géocodage inversé | Particularité |
|--------------------------------------|:---:|:---:|:---:|---|
| Adresse — Base Adresse Nationale (BAN) | `fra` | ✅ | ✅ | Client officiel de la BAN |
| Photon (OpenStreetMap)                | `pho` | ✅ | ✅ | Source alternative, hors Géoplateforme |
| Parcelle cadastrale (Géoplateforme, index `parcel`) | `par` | ✅ | ✅ | Widget de recherche structurée (département → commune → section → numéro) |
| Bâtiment — Référentiel National du Bâti (RNB) | `rnb` | ✅ | ✅ | Le résultat inversé est enrichi avec l'adresse du bâtiment ; couche de tuiles vectorielles RNB ajoutable en un clic pour vérifier visuellement le résultat |

Pour chaque source : recherche via la barre de recherche universelle, dockwidget de géocodage inversé (sélection d'un point sur la carte), et traitements Processing en lot (couche entière, direct ou inversé).

## Code source 

[ Code source](https://github.com/IGNF-Xavier/qgis-French-locator-filter)

## Others languages


