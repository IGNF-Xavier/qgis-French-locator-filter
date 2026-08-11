- Description :

Géocodage inversé de parcelle cadastrale (index `parcel`) avec la Géoplateforme depuis une couche vectorielle.

- Paramètres :

| Entrée           | Paramètre          | Description                                                |
|------------------|--------------------|------------------------------------------------------------|
| Couche vectorielle en entrée   | `INPUT`        | Couche vectorielle en entrée (type point ou polygone).  |
| Nombre de résultat par ligne     | `NB_RESULT_BY_FEATURE`      | Limitation du nombre de résultat par ligne (défaut 1). |

- Sorties :

| Sortie                             | Paramètre                           | Description                    |
|------------------------------------|-------------------------------------|--------------------------------|
| Couche vectorielle en sortie | `OUTPUT`        | Couche vectorielle avec la parcelle trouvée par géocodage inversé.  |

Nom du traitement : `french_locator_filter:gpf_parcel_inverse_geocoder_batch`
