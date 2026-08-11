- Description :

Géocodage inversé avec la Géoplateforme depuis une couche vectorielle, en utilisant le ou les index actifs configurés dans les réglages du plugin (adresse, POI, parcelle...).

- Paramètres :

| Entrée           | Paramètre          | Description                                                |
|------------------|--------------------|------------------------------------------------------------|
| Couche vectorielle en entrée   | `INPUT`        | Couche vectorielle en entrée (type point ou polygone).  |
| Nombre de résultat par ligne     | `NB_RESULT_BY_FEATURE`      | Limitation du nombre de résultat par ligne (défaut 1). |

- Sorties :

| Sortie                             | Paramètre                           | Description                    |
|------------------------------------|-------------------------------------|--------------------------------|
| Couche vectorielle en sortie | `OUTPUT`        | Couche vectorielle avec géocodage inversé, colonnes de tous les index actifs.  |

Nom du traitement : `french_locator_filter:gpf_dynamic_inverse_geocoder_batch`
