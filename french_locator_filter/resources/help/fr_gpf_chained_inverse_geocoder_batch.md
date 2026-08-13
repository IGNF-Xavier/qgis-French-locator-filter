- Description :

Géocodage inversé chaîné (point → bâtiment RNB → parcelle(s) cadastrale(s), avec adresse embarquée) depuis une couche vectorielle. Un bâtiment pouvant intersecter plusieurs parcelles, plusieurs lignes en sortie peuvent correspondre à une même ligne en entrée.

- Paramètres :

| Entrée           | Paramètre          | Description                                                |
|------------------|--------------------|------------------------------------------------------------|
| Couche vectorielle en entrée   | `INPUT`        | Couche vectorielle en entrée (type point ou polygone).  |
| Nombre de résultat par ligne     | `NB_RESULT_BY_FEATURE`      | Limitation du nombre de résultat par ligne (défaut 1). |

- Sorties :

| Sortie                             | Paramètre                           | Description                    |
|------------------------------------|-------------------------------------|--------------------------------|
| Couche vectorielle en sortie | `OUTPUT`        | Couche vectorielle avec les attributs adresse, bâtiment et parcelle fusionnés.  |

Nom du traitement : `french_locator_filter:gpf_chained_inverse_geocoder_batch`
