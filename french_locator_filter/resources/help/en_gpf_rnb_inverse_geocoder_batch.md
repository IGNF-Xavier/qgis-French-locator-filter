- Description:

Reverse geocoding using the Référentiel National du Bâti (RNB) from a vector layer: finds the nearby building(s) for each point, together with their address.

- Parameters:

| Input                  | Parameter | Description                                              |
|-------------------------|-----------|----------------------------------------------------------|
| Input vector layer      | `INPUT`   | Input vector layer (point or polygon type).                         |
| Number of result for each feature     | `NB_RESULT_BY_FEATURE`      | Limitation of result number for each feature (default 1). |

- Outputs:

| Output                  | Parameter | Description                                  |
|--------------------------|-----------|----------------------------------------------|
| Output vector layer      | `OUTPUT`  | Vector layer with the found building(s) and their address. |

Processing name: `french_locator_filter:gpf_rnb_inverse_geocoder_batch`
