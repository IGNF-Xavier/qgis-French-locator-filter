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

Pour chaque source : recherche via la barre de recherche universelle, dockwidget de géocodage inversé (sélection d'un point sur la carte, résultats affichés dans un tableau à une colonne par attribut, colonnes réordonnables par glisser-déposer), et traitements Processing en lot (couche entière, direct ou inversé). Les traitements Processing s'appuient sur les mêmes classes de géocodeur que les widgets interactifs : toute correction ou évolution de la logique décrite ci-dessous s'applique donc identiquement en ModelBuilder.

## Logique de géocodage direct et inversé

Détail de ce que fait chaque source lors d'une recherche par texte (géocodage direct) ou par point cliqué sur la carte (géocodage inversé).

### Adresse — BAN (`fra`)

- **Direct** : appel `GET /search` de l'API Géoplateforme (données de la Base Adresse Nationale), avec le texte saisi comme requête libre.
- **Inversé** : appel `GET /reverse` avec les coordonnées du point cliqué et `limit=1` explicite, pour ne remonter que l'adresse la plus proche (l'API renvoie jusqu'à 10 résultats par défaut si `limit` n'est pas précisé).

### Photon — OpenStreetMap (`pho`)

- **Direct** : appel `GET /api` de l'instance Photon (recherche libre, hors Géoplateforme, basée sur les données OpenStreetMap).
- **Inversé** : appel `GET /reverse` de la même API avec les coordonnées du point cliqué.

### Parcelle cadastrale (`par`)

- **Direct**, deux modes :
  - recherche libre depuis la barre de recherche : `GET /search?index=parcel` avec le texte saisi ;
  - recherche structurée depuis le widget dédié (département → commune, la liste des communes étant récupérée via `geo.api.gouv.fr` → section → numéro) : appel du même index mais avec des paramètres structurés (`departmentcode`, `municipalitycode`, `section`, `number`) plutôt qu'une requête libre ; le numéro de parcelle est complété à 4 chiffres (`"183"` → `"0183"`) et le code commune est utilisé sans son préfixe département, conformément au format attendu par l'API.
- **Inversé** : `GET /reverse?index=parcel` avec `limit=1`, pour ne renvoyer que la parcelle contenant le point cliqué (et non toutes les parcelles voisines dans le rayon de recherche par défaut).

### Bâtiment — RNB (`rnb`)

Le RNB n'offre ni recherche libre ni recherche point+rayon : ce géocodeur combine donc deux API indépendantes.

- **Direct** : le texte saisi est d'abord résolu en adresse via l'index adresse de la Géoplateforme (`/search`), puis l'identifiant BAN de cette adresse (`cle_interop_ban`) sert à interroger `GET /buildings/` du RNB pour récupérer le ou les bâtiments à cette adresse.
- **Inversé** : `GET /buildings/` du RNB est interrogé avec une petite emprise (`bbox`, ~40 m) autour du point cliqué ; les bâtiments candidats sont ensuite triés — ceux dont l'empreinte contient le point d'abord, les autres par distance croissante. Chaque bâtiment RNB embarque déjà l'adresse à laquelle il est rattaché : elle est utilisée directement pour enrichir le résultat, sans requête supplémentaire vers la BAN.

### Géoplateforme — index configurables (`gpf`)

- **Direct** : un seul appel `GET /search?index=...` avec la liste des index actifs choisis dans les réglages (adresse, POI, parcelle) ; chaque résultat est typé par le champ `_type` de la réponse, exposé dans la colonne `result_index` (utile pour les index parcelle/POI, qui n'ont pas de colonne "type" native contrairement à l'index adresse).
- **Inversé** : `GET /reverse?index=...` avec `limit` égal au nombre d'index actifs (au moins 1), pour obtenir un résultat pertinent par index sans être noyé par le rayon de recherche par défaut de l'API.

### Fiche complète (`fic`)

Chaîne adresse → parcelle cadastrale → bâtiment RNB en une seule recherche, en s'appuyant sur les couches WFS `BAN-PLUS` de la Géoplateforme (liens précalculés adresse↔parcelle et bâtiment↔parcelle) et sur la couche PCI `parcellaire express`, plutôt que sur une reconstruction heuristique par recherche géométrique. Comme une adresse peut être liée à plusieurs parcelles, et une parcelle à plusieurs bâtiments, le géocodeur retourne un résultat distinct par combinaison (adresse, parcelle, bâtiment) — l'équivalent d'une jointure SQL — plutôt que de compresser des listes dans un seul attribut.

- **Direct** :
  1. l'adresse est résolue via la BAN (`/search`) ;
  2. son identifiant (`id_adr`) est recherché dans la couche WFS `lien_adresse_parcelle` pour obtenir la ou les parcelle(s) liée(s), avec le niveau de confiance du lien (`type_lien` : `BAN` = lien déclaré fiable, `GEO` = inféré géométriquement — exposé en colonne `parcel_type_lien`) ;
  3. pour chaque parcelle : récupération de sa géométrie réelle (WFS PCI `parcelle`), des bâtiments RNB dessus (`GET /buildings/plot/{idu}/`), des identifiants BDTOPO liés via la couche WFS `lien_bati_parcelle` (colonne `building_ext_bdtopo_id_wfs`) et via les `ext_ids` propres à chaque bâtiment RNB (colonne `building_ext_bdtopo_id_rnb`, indépendante de la précédente), ainsi que des bâtiments PCI ("bâti parcellaire", couche WFS `batiment`) qui intersectent réellement la parcelle.
- **Inversé** :
  1. les parcelles candidates sont recherchées directement par géométrie autour du point cliqué (bbox sur la couche WFS PCI `parcelle`), triées par containment puis distance ;
  2. l'adresse au point cliqué est résolue via la BAN inversée (`limit=1`) ;
  3. pour chaque parcelle retenue, les mêmes étapes bâtiment RNB / BDTOPO / bâti cadastral que pour la recherche directe sont exécutées ; `parcel_type_lien` reste vide, la parcelle étant trouvée par géométrie et non via le lien adresse↔parcelle.

## Code source

[Code officiel à l'origine Gitlab Oslandia](https://gitlab.com/Oslandia/qgis/french_locator_filter)
