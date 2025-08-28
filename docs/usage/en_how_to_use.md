# User Guide

Place search extension (geocoding) using the Géoplateforme geocoding API <https://geoservices.ign.fr/documentation/services/services-geoplateforme/geocodage>.

This extension enables place search by address in [the QGIS universal search bar (Locator)](https://docs.qgis.org/3.40/en/docs/user_manual/introduction/qgis_configuration.html#locator-settings).

A tool is available to perform reverse geocoding (get an address from coordinates).

Processing algorithms are also available to run batch operations from a vector layer.

## Geocoding usage

1. Freely type an address search in the search bar (bottom left of the QGIS window)  
2. Select a result. Double-click or press Enter to move the map to the chosen address  

![Address search in QGIS](/_static/images/french_locator_sample_basque_qgis_details.png "Example of a search with the word 'basque' in the QGIS locator")

### Notes

#### Prefix

Typing the prefix `fra` restricts the search to addresses provided by this service (and avoids searching other objects indexed by the Locator bar).

#### Predefined zoom levels

The API does not return a bounding box that allows an exact zoom. Predefined zoom levels are set depending on the type of result:

- 1/25,000 (city)  
- 1/5,000 (street)  
- 1/2,000 (precise address)  

----

## Reverse geocoding usage

An address search tool from a point is available in the toolbar after installing the plugin.

![Toolbar of French Locator Filter](/_static/images/french_locator_toolbar.png "'Toolbar of French Locator Filter")

A dock widget is displayed allowing you to select a point on the map and request an address search:

![Reverse geocoding](/_static/images/french_locator_reverse_geocode_widget.png "Reverse geocoding")

----

## Settings

The settings used by the plugin are integrated into the QGIS Preferences menu:

![Settings of French Locator Filter](/_static/images/french_locator_settings.png "'Settings of French Locator Filter")

Some information cannot be modified by the end user.

### Environment variables

These parameters can be defined via environment variables. This allows plugin configuration to be managed directly by the IT Department.

The following table lists the available parameters with their associated environment variable and default value:

|Parameter                                      | Environment variable                           | Default value                               |
|-----------------------------------------------|------------------------------------------------|---------------------------------------------|
|Géoplateforme API request URL                  | `QGIS_FRENCH_LOCATOR_REQUEST_URL`              | `https://data.geopf.fr/geocodage/`          |
|Default parameters for Géoplateforme API query | `QGIS_FRENCH_LOCATOR_REQUEST_URL_QUERY`        | `limit=10&autocomplete=1`                   |
|Photon API request URL                         | `QGIS_FRENCH_LOCATOR_REQUEST_PHOTON_URL`       | `https://photon.komoot.io/api/`             |
|Default parameters for Photon API query        | `QGIS_FRENCH_LOCATOR_REQUEST_PHOTON_URL_QUERY` | `limit=10&lang=fr`                          |
