- Description :

Géocodage chaîné (adresse Géoplateforme → bâtiment RNB → parcelle(s) cadastrale(s)) depuis une couche vectorielle de type point. Un bâtiment pouvant intersecter plusieurs parcelles, plusieurs lignes en sortie peuvent correspondre à une même ligne en entrée.

- Paramètres :

| Entrée           | Paramètre          | Description                                                |
|------------------|--------------------|------------------------------------------------------------|
| Couche vectorielle en entrée   | `INPUT`        | Couche vectorielle en entrée |
| Attribut adresse      | `FIELD`      | Nom de l'attribut utilisé pour la définition de l'adresse. |

- Sorties :

| Sortie                             | Paramètre                           | Description                    |
|------------------------------------|-------------------------------------|--------------------------------|
| Couche vectorielle en sortie | `OUTPUT`        | Couche vectorielle avec les attributs adresse, bâtiment et parcelle fusionnés.  |

Nom du traitement : `french_locator_filter:gpf_chained_geocoder_batch`
