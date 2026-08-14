# French Locator Filter - Un plugin de géocodage pour QGIS - version test

## Fonctionnalités

Le plugin ajoute un filtre dans la barre de recherche universelle (Localisateur) de QGIS, un dock de géocodage inversé, et des traitements Processing en lot, pour six sources de géocodage :

| Source                              | Préfixe locator | Géocodage direct | Géocodage inversé | Particularité |
|--------------------------------------|:---:|:---:|:---:|---|
| Adresse — Base Adresse Nationale (BAN) | `fra` | ✅ | ✅ | Client officiel de la BAN |
| Photon (OpenStreetMap)                | `pho` | ✅ | ✅ | Source alternative, hors Géoplateforme |
| Parcelle cadastrale (Géoplateforme, index `parcel`) | `par` | ✅ | ✅ | Widget de recherche structurée (département → commune → section → numéro) |
| Bâtiment — Référentiel National du Bâti (RNB) | `rnb` | ✅ | ✅ | Le résultat inversé est enrichi avec l'adresse du bâtiment ; couche de tuiles vectorielles RNB ajoutable en un clic pour vérifier visuellement le résultat |
| Géoplateforme (index configurables)   | `gpf` | ✅ | ✅ | Index actifs (adresse, POI, parcelle) choisis dans les réglages, pilotés par le `GetCapabilities` du service |
| Fiche complète (adresse + bâtiment + parcelle) | `fic` | ✅ | ✅ | Chaîne adresse → parcelle → bâtiment RNB via les couches WFS précalculées de la Géoplateforme (`BAN-PLUS`, PCI parcellaire) ; un résultat par combinaison lorsque plusieurs bâtiments/parcelles sont liés |

Pour chaque source : recherche via la barre de recherche universelle, dockwidget de géocodage inversé (sélection d'un point sur la carte, résultats affichés dans un tableau à une colonne par attribut), et traitements Processing en lot (couche entière, direct ou inversé).

### Fiche complète (`fic`)

Cette source combine en une seule recherche :

- l'adresse (Base Adresse Nationale) ;
- la ou les parcelle(s) cadastrale(s) liée(s), avec leur emprise réelle (section, numéro, feuille, contenance) ;
- le ou les bâtiment(s) RNB sur chaque parcelle, ainsi que leurs identifiants externes (BDTOPO, bâti cadastral PCI).

Elle s'appuie sur les couches WFS `BAN-PLUS` de la Géoplateforme (liens précalculés adresse↔parcelle et bâtiment↔parcelle) plutôt que sur une reconstruction heuristique, et sur l'API du RNB pour le détail des bâtiments.

## Code source

[Code officiel à l'origine Gitlab Oslandia](https://gitlab.com/Oslandia/qgis/french_locator_filter)
