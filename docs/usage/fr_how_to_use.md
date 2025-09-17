# Guide d'utilisation

Extension de recherche de lieux (géocodage) utilisant l'API de géocodage de la Géoplateforme <https://geoservices.ign.fr/documentation/services/services-geoplateforme/geocodage>.

Cette extension permet d'activer la recherche de lieu par adresse dans [la barre de recherche universelle de QGIS (Localisateur)](https://docs.qgis.org/3.40/fr/docs/user_manual/introduction/qgis_configuration.html#locator-settings).

Un outil est disponible pour effectuer un géocodage inversé (adresse depuis coordonnées).

Des processings sont aussi disponibles pour des traitements en lots à partir d'une couche vectorielle.

## Utilisation géocodage

1. taper librement une recherche d'adresse dans la barre de recherche (en bas à gauche de la fenêtre QGIS)
2. Sélectionner un résultat. Double clic ou entrée déplace la carte sur l'adresse retenue

![Recherche d'adresse dans QGIS](/_static/images/french_locator_sample_basque_qgis_details.png "Exemple de recherche sur le mot 'basque' dans le localisateur de QGIS")

### Notes

#### Préfixe

Taper le préfixe `fra` permet de ne rechercher que des adresses fournies par ce service (et évite de rechercher les autres objets indexés par la barre Localisateur).

#### Zooms prédéfinis

L'API ne renvoie pas d'emprise permettant de zoomer exactement. Les zooms prédéfinis sont pré-définis en fonction du type de résultat :

- 1/25 000 (ville)
- 1/5000 (rue)
- 1/2000 (adresse précise)

----

## Utilisation géocodage inversé

Un outil de recherche d'adresse depuis un point est disponible dans la barre d'outil après installation du plugin.

![Toolbar of French Locator Filter](/_static/images/french_locator_toolbar.png "'Toolbar of French Locator Filter")

Un dockwidget est affiché permettant de sélectionner un point sur la carte et demander une recherche d'adresse:

![Géocodage inversé](/_static/images/french_locator_reverse_geocode_widget.png "Géocodage inversé")

Il est possible de charger le résultat dans une couche temporaire via le bouton `Charger`.

----

## Réglages

Les réglages utilisés par le plugin sont intégrés au menu des Préférences de QGIS :

![Settings of French Locator Filter](/_static/images/french_locator_settings.png "'Settings of French Locator Filter")

Certaines informations ne sont pas modifiables par l'utilisateur final.

### Variables d'environnement

Ces paramètres peuvent être définis via des variables d'environnement. Ceci permet une configuration du plugin directement par la Direction des Systèmes d'Information (DSI).

Le tableau suivant reprend les paramètres disponibles avec la variable d'environnement associée et la valeur par défaut:

|Paramètre                                      | Variable d'environnement                       | Valeur par défaut                          |
|-----------------------------------------------|------------------------------------------------|--------------------------------------------|
|URL requête API Géoplateforme                  | `QGIS_FRENCH_LOCATOR_REQUEST_URL`              | `https://data.geopf.fr/geocodage/` |
|Paramètre par défaut requête API Géoplateforme | `QGIS_FRENCH_LOCATOR_REQUEST_URL_QUERY`        | `limit=10&autocomplete=1`                  |
|URL requête API Photon                         | `QGIS_FRENCH_LOCATOR_REQUEST_PHOTON_URL`       | `https://photon.komoot.io/api/`            |
|Paramètre par défaut requête API Photon        | `QGIS_FRENCH_LOCATOR_REQUEST_PHOTON_URL_QUERY` | `limit=10&lang=fr`                         |
