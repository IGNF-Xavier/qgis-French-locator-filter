- Description :

Géocodage avec la Géoplateforme depuis une couche vectorielle de type point, en utilisant le ou les index actifs configurés dans les réglages du plugin (adresse, POI, parcelle...).

- Paramètres :

| Entrée           | Paramètre          | Description                                                |
|------------------|--------------------|------------------------------------------------------------|
| Couche vectorielle en entrée   | `INPUT`        | Couche vectorielle en entrée |
| Attribut adresse      | `FIELD`      | Nom de l'attribut utilisé pour la recherche. |

- Sorties :

| Sortie                             | Paramètre                           | Description                    |
|------------------------------------|-------------------------------------|--------------------------------|
| Couche vectorielle en sortie | `OUTPUT`        | Couche vectorielle géocodée, avec les colonnes de tous les index actifs.  |

Nom du traitement : `french_locator_filter:gpf_dynamic_geocoder_batch`
