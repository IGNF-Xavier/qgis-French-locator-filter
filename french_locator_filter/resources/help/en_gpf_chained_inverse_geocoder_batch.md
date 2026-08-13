- Description:

Chained reverse geocoding (point → RNB building → cadastral parcel(s), with embedded address) from a vector layer. Since a building can intersect several parcels, several output rows can correspond to a single input row.

- Parameters:

| Input                  | Parameter | Description                                              |
|-------------------------|-----------|----------------------------------------------------------|
| Input vector layer      | `INPUT`   | Input vector layer (point or polygon type).                         |
| Number of result for each feature     | `NB_RESULT_BY_FEATURE`      | Limitation of result number for each feature (default 1). |

- Outputs:

| Output                  | Parameter | Description                                  |
|--------------------------|-----------|----------------------------------------------|
| Output vector layer      | `OUTPUT`  | Vector layer with merged address, building and parcel attributes. |

Processing name: `french_locator_filter:gpf_chained_inverse_geocoder_batch`
