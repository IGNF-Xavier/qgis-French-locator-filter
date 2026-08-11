- Description :

Géocodage de bâtiment avec le Référentiel National du Bâti (RNB) depuis une couche vectorielle de type point. La recherche résout d'abord l'adresse via la Géoplateforme puis interroge le RNB pour le bâtiment correspondant.

- Paramètres :

| Entrée           | Paramètre          | Description                                                |
|------------------|--------------------|------------------------------------------------------------|
| Couche vectorielle en entrée   | `INPUT`        | Couche vectorielle en entrée |
| Attribut adresse      | `FIELD`      | Nom de l'attribut utilisé pour la définition de l'adresse. |

- Sorties :

| Sortie                             | Paramètre                           | Description                    |
|------------------------------------|-------------------------------------|--------------------------------|
| Couche vectorielle en sortie | `OUTPUT`        | Couche vectorielle avec le bâtiment trouvé et son adresse.  |

Nom du traitement : `french_locator_filter:gpf_rnb_geocoder_batch`
