# Guide d'utilisation

Extension de recherche de lieux (géocodage) utilisant l'API de la Base Adresse Nationale de la France <https://geo.api.gouv.fr/adresse/>.

Cette extension permet d'activer la recherche de lieu par adresse dans [la barre de recherche universelle de QGIS (Localisateur)](https://docs.qgis.org/3.16/fr/docs/user_manual/introduction/qgis_configuration.html#locator-settings).

## Utilisation

1. taper librement une recherche d'adresse dans la barre de recherche (en bas à gauche de la fenêtre QGIS)
2. Sélectionner un résultat. Double clic ou entrée déplace la carte sur l'adresse retenue

![Recherche d'adresse dans QGIS](/_static/images/french_locator_sample_basque_qgis_details.png "Exemple de recherche sur le mot 'basque' dans le localisateur de QGIS")

## Notes

### Préfixe

Taper le préfixe `fra` permet de ne rechercher que des adresses fournies par ce service (et évite de rechercher les autres objets indexés par la barre Localisateur).

### Zooms prédéfinis

L'API ne renvoie pas d'emprise permettant de zoomer exactement. Les zooms prédéfinis sont pré-définis en fonction du type de résultat :

- 1/25 000 (ville)
- 1/5000 (rue)
- 1/2000 (adresse précise)

----

## Réglages

Les réglages utilisés par le plugin sont intégrés au menu des Préférences de QGIS :

![Settings of French Locator Filter](/_static/images/french_locator_settings.png "'Settings of French Locator Filter")

Certaines informations ne sont pas modifiables par l'utilisateur final.
