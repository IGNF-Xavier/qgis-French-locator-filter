- Description:

Building geocoding using the Référentiel National du Bâti (RNB) from a point vector layer. The search first resolves the address via Géoplateforme, then queries RNB for the matching building.

- Parameters:

| Input                  | Parameter | Description                                              |
|-------------------------|-----------|----------------------------------------------------------|
| Input vector layer      | `INPUT`   | Input vector layer.                         |
| Address attribute       | `FIELD`   | Name of the attribute used for the address definition.   |

- Outputs:

| Output                  | Parameter | Description                                  |
|--------------------------|-----------|----------------------------------------------|
| Output vector layer      | `OUTPUT`  | Vector layer with the found building and its address. |

Processing name: `french_locator_filter:gpf_rnb_geocoder_batch`
