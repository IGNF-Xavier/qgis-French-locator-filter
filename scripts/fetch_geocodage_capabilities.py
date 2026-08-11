#! python3

"""Script to fetch the Géoplateforme geocoding service GetCapabilities and embed
it as a static snapshot in the plugin resources, so the dynamic geocoder
(GpfDynamicGeocoder) has a usable index/schema list out of the box, without
requiring a network call on first use.

This script is intended to be run from the root of the project, before
packaging (see .gitlab-ci.yml, job build:plugin), and has no PyQGIS
dependency since it also runs outside of QGIS in CI.
"""

# -- Imports
import json
import urllib.request
from pathlib import Path

# -- Variables
CAPABILITIES_URL = "https://data.geopf.fr/geocodage/getcapabilities"
output_file = Path("french_locator_filter/resources/geocodage_capabilities.json")

# -- Run
with urllib.request.urlopen(CAPABILITIES_URL, timeout=30) as response:
    capabilities = json.loads(response.read().decode("utf-8"))

with output_file.open("w", encoding="utf-8") as f:
    json.dump(capabilities, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"Wrote {output_file} ({len(capabilities.get('indexes', []))} indexes)")
