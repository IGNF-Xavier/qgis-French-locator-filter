- Description:

Reverse geocoding using Géoplateforme from a vector layer, using the active index(es) configured in the plugin settings (address, poi, parcel...).

- Parameters:

| Input                  | Parameter | Description                                              |
|-------------------------|-----------|----------------------------------------------------------|
| Input vector layer      | `INPUT`   | Input vector layer (point or polygon type).                         |
| Number of result for each feature     | `NB_RESULT_BY_FEATURE`      | Limitation of result number for each feature (default 1). |

- Outputs:

| Output                  | Parameter | Description                                  |
|--------------------------|-----------|----------------------------------------------|
| Output vector layer      | `OUTPUT`  | Vector layer with reverse geocoding, columns from all active indexes. |

Processing name: `french_locator_filter:gpf_dynamic_inverse_geocoder_batch`
