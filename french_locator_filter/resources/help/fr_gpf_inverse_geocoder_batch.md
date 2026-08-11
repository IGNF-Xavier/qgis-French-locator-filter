- Description :

Géocodage inversé avec la Géoplateforme depuis une couche vectorielle.

- Paramètres :

| Entrée           | Paramètre          | Description                                                |
|------------------|--------------------|------------------------------------------------------------|
| Couche vectorielle en entrée   | `INPUT`        | Couche vectorielle en entrée (type point ou polygone).  |
| Nombre de résultat par ligne     | `NB_RESULT_BY_FEATURE`      | Limitation du nombre de résultat par ligne (défaut 1). |

- Sorties :

| Sortie                             | Paramètre                           | Description                    |
|------------------------------------|-------------------------------------|--------------------------------|
| Couche vectorielle en sortie | `OUTPUT`        | Couche vectorielle avec géocodage inversé.  |

Nom du traitement : `french_locator_filter:gpf_inverse_geocoder_batch`
