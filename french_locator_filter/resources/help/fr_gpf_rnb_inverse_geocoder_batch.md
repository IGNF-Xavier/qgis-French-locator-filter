- Description :

Géocodage inversé avec le Référentiel National du Bâti (RNB) depuis une couche vectorielle : recherche du/des bâtiment(s) à proximité de chaque point, avec l'adresse associée.

- Paramètres :

| Entrée           | Paramètre          | Description                                                |
|------------------|--------------------|------------------------------------------------------------|
| Couche vectorielle en entrée   | `INPUT`        | Couche vectorielle en entrée (type point ou polygone).  |
| Nombre de résultat par ligne     | `NB_RESULT_BY_FEATURE`      | Limitation du nombre de résultat par ligne (défaut 1). |

- Sorties :

| Sortie                             | Paramètre                           | Description                    |
|------------------------------------|-------------------------------------|--------------------------------|
| Couche vectorielle en sortie | `OUTPUT`        | Couche vectorielle avec le(s) bâtiment(s) trouvé(s) et leur adresse.  |

Nom du traitement : `french_locator_filter:gpf_rnb_inverse_geocoder_batch`
