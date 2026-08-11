- Description :

Géocodage de parcelle cadastrale (index `parcel`) avec la Géoplateforme depuis une couche vectorielle de type point.

- Paramètres :

| Entrée           | Paramètre          | Description                                                |
|------------------|--------------------|------------------------------------------------------------|
| Couche vectorielle en entrée   | `INPUT`        | Couche vectorielle en entrée |
| Attribut de recherche      | `FIELD`      | Nom de l'attribut utilisé pour la recherche de parcelle (identifiant cadastral). |

- Sorties :

| Sortie                             | Paramètre                           | Description                    |
|------------------------------------|-------------------------------------|--------------------------------|
| Couche vectorielle en sortie | `OUTPUT`        | Couche vectorielle avec géocodage de la parcelle.  |

Nom du traitement : `french_locator_filter:gpf_parcel_geocoder_batch`
