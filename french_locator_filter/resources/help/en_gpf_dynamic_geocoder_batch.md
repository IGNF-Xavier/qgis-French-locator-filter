- Description:

Geocoding using Géoplateforme from a point vector layer, using the active index(es) configured in the plugin settings (address, poi, parcel...).

- Parameters:

| Input                  | Parameter | Description                                              |
|-------------------------|-----------|----------------------------------------------------------|
| Input vector layer      | `INPUT`   | Input vector layer.                         |
| Address attribute       | `FIELD`   | Name of the attribute used for the search.   |

- Outputs:

| Output                  | Parameter | Description                                  |
|--------------------------|-----------|----------------------------------------------|
| Output vector layer      | `OUTPUT`  | Geocoded vector layer, with columns from all active indexes. |

Processing name: `french_locator_filter:gpf_dynamic_geocoder_batch`
