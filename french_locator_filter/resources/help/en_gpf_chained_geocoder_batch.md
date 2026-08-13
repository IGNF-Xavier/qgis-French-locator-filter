- Description:

Chained geocoding (Géoplateforme address → RNB building → cadastral parcel(s)) from a point vector layer. Since a building can intersect several parcels, several output rows can correspond to a single input row.

- Parameters:

| Input                  | Parameter | Description                                              |
|-------------------------|-----------|----------------------------------------------------------|
| Input vector layer      | `INPUT`   | Input vector layer.                         |
| Address attribute       | `FIELD`   | Name of the attribute used for the address definition.   |

- Outputs:

| Output                  | Parameter | Description                                  |
|--------------------------|-----------|----------------------------------------------|
| Output vector layer      | `OUTPUT`  | Vector layer with merged address, building and parcel attributes. |

Processing name: `french_locator_filter:gpf_chained_geocoder_batch`
