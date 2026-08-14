# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.6.2-exp - 2026-08-14

- fix(geocoder): send an explicit `limit=` on the dynamic geocoder's reverse geocoding requests (1 per active index, at least 1) instead of letting the API default to `limit=10`, which flooded the interactive reverse geocoding dock with unrelated nearby candidates

## 1.6.1-exp - 2026-08-13

- feat(geocoding): add a chained geocoder (locator filter `fic`, reverse geocoding dock entry, batch Processing algorithms) combining address (BAN), RNB building and cadastral parcel(s) into a single "fiche complète" lookup, using the RNB `withPlots=1` parameter to get the intersecting parcel(s) without an extra API call; since a building can intersect several parcels, one result is emitted per (address, building, parcel) combination rather than squeezing a list into one attribute

## 1.6.0-exp - 2026-08-12

- feat(geocoding): add direct and reverse geocoding for the cadastral parcel index (`index=parcel`) of the Géoplateforme API, including locator filter, reverse geocoding dock entry and batch Processing algorithms
- feat(geocoding): add a structured parcel search widget (department → commune → section → number)
- feat(geocoding): add direct and reverse geocoding for the Référentiel National du Bâti (RNB), including locator filter, reverse geocoding dock entry and batch Processing algorithms; reverse results are enriched with the building's address, embedded directly in the RNB response
- refactor(geocoder): share the Géoplateforme host rate-limit counter between the address and parcel geocoders
- feat(geocoding): add a dynamic Géoplateforme geocoder (locator filter `gpf`, reverse geocoding dock entry, batch Processing algorithms) whose active index(es) — address, poi, parcel — are configurable in the plugin settings instead of hardcoded, driven by the service's GetCapabilities schema (embedded in the plugin package and refreshable from the settings page); resolves [#31](https://gitlab.com/Oslandia/qgis/french_locator_filter/-/issues/31) for the `/search` and `/reverse` routes (CSV batch routes deferred, see #37)
- feat(menu): add "Ajouter la couche RNB (bâtiments)" action and automatic loading of the RNB vector tile layer on first RNB reverse geocoding, to visually check results
- fix(geocoder): send an explicit `limit=1` on parcel reverse geocoding requests (the API otherwise defaults to `limit=10`, returning many unrelated nearby parcels)
- fix(geocoder): zero-pad the parcel number to 4 digits and strip the department prefix from the municipality code in the structured parcel search, matching the API's expected format

## 1.5.0 - 20226-03-09

- New logo by @florentfougeres
- Declare plugin compatible with qgis4 by @geojulien
- update(UI): add menu "Géocodage" for plugin actions by @jmkerloch
- feat(geocoder): define attributes types by @jmkerloch
- feat(reverse geocoding): allow selection of geocoder for reverse geocoding by @jmkerloch
- feat(batch): add batch processing with Photon geocoder by @jmkerloch
- feat(geocoding): add new function to define request param and result content by @jmkerloch
- feat(test): add mock for gpf server to be able to run test without internet connection by @jmkerloch
- fix(geocoding): use settings search_terms_to_ignore to limit search terms by @jmkerloch
- fix(geocoding): remove duplicated slash by @jmkerloch
- update(docs): add hyperlink to official tutorial on adresse.data.gouv.fr by @geojulien
- update(docs): distinguish release from current version by @geojulien
- add(docs): auto generate QDT snippet and use keepachangelog to retrieve latest published version from CHANGELOG.md by @geojulien
- add(docs): ajout section "plugin officiel" by @geojulien

## 1.4.1 - 2025-09-18

- feature: store geocoding result export to a memory layer (see !53)
- fix: no reportError function available for QgsFeedback (misused as QgsProcessingFeedback) !52
- fix: QMenu need a parent in Qt6 for correct use !54

## 1.4.0 - 2025-09-05

- New feature: add reverse geocoding processing and UI !49

## 1.3.0 - 2025-05-16

New implementation of QgsLocatorFilter using QgsGeocoderInterface. Adds a processing for batch geocoding.

- feat(geocoder): implement QgsGeocoderInterface for photon and BAN !30 #21
- feat(batch): add batch processing for FrenchBanGeocoder !37 #17
- feat(gpf): add function create_gpf_plugins_actions to be called by geoplateforme plugin !46
- feat(rest api): limit number of request per seconds (10 for photon, 50 for gpf)  !47 #29

## 1.2.0 - 2025-04-25

- project: set minimal QGIS version to 3.40.4
- feature: make plugin compatible with Qt6 (QGIS 4) #25 !34 !40
- feature: use the new endpoint for French BAN API #20 !41
- ci: modernize workflow !38
- fix: use new way to retrieve QgsLocatorResult._userData() to fix warnings !42
- tooling: bump dependencies !43
- contributors: Landry Breuil, Nicolas Godet, Jean-Marie Kerloch, Julien Moura

## 1.1.1 - 2024-06-12

- ValueError lors du déchargement du plugin #23

## 1.1.0 - 2024-02-09

- Add new locator with Photon API by Jean-Marie KERLOCH #19
- Fix min search length by Rémi Desgrange - !27
- Add help path and key to connect plugin documentation to standard help button in settings view by Julien Moura - !28

## 1.0.4 - 2022-10-20

- Handle special search terms to API - #9
- Reduce cases where a bug that can lead to a QGIS crash because of legacy method
- Add a button to reset settings to factory default
- Clean legacy code

## 1.0.3 - 2022-10-18

- change minimal search length See #8 - !20 by @nicogodet
- map report button to the bug issue template
- prevent Sonar run on forks
- dependencies update

## 1.0.2 - 2022-04-13

- add unit test running on QGIS
- improve settings management
- update dependencies

## 1.0.1 - 2022-01-03

- minor improvments on code quality
- better documentation

## 1.0.0 - 2021-06-17

- minor fix on settings dialog UI
- stable release

## 1.0.0-beta2 - 2021-06-11

- add debug mode
- small typo fixes #5
- minor improvments

## 1.0.0-beta1 - 2021-06-02

- use QGIS 3.16 abilities (especially on networking)
- apply Oslandia code quality standards (development tooling, documentation, CI, etc.)
- add settings: display used values and allow end-user customize some preferences
- fix deprecation warning on QgsCoordinateReferenceSystem

## 0.2.0 - 2020-03-17

- adds insee code display to municipalities

## 0.1.0 - 2019-10-08

- first version
