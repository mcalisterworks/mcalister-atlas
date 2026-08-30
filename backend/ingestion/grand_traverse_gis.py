import requests


# ---------------------------------------------------------------------------
# Grand Traverse County Tax Parcel GIS
# ---------------------------------------------------------------------------

LAYER_URL = (
    "https://gis.gtcountymi.gov/"
    "arcgis/rest/services/Public_Services/"
    "Tax_Parcel_Public/MapServer/0"
)

QUERY_URL = f"{LAYER_URL}/query"


# ---------------------------------------------------------------------------
# GIS Layer Metadata
# ---------------------------------------------------------------------------

def get_layer_info() -> dict:
    """Retrieve metadata about the ArcGIS parcel layer."""

    response = requests.get(
        LAYER_URL,
        params={"f": "json"},
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------------------------
# Parcel Query
# ---------------------------------------------------------------------------

def fetch_parcels(
    where: str = "1=1",
    limit: int = 10,
) -> dict:
    """
    Query Grand Traverse County parcels.

    Parameters
    ----------
    where:
        ArcGIS SQL WHERE clause.

        Examples:
            "1=1"
            "PARCELID='01-001-001-00'"
            "ASSACRES > 10"

    limit:
        Maximum number of parcels to return.
    """

    params = {
        "where": where,
        "outFields": "*",
        "returnGeometry": "true",
        "resultRecordCount": limit,
        "f": "geojson",
    }

    response = requests.get(
        QUERY_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    # ArcGIS can return an error object with HTTP 200.
    if "error" in data:
        raise RuntimeError(
            f"ArcGIS query failed: {data['error']}"
        )

    return data


# ---------------------------------------------------------------------------
# Display Functions
# ---------------------------------------------------------------------------

def print_layer_info(layer_info: dict) -> None:
    """Print useful information about the GIS layer."""

    print("\n--- GIS LAYER ---")

    print("Name:", layer_info.get("name"))
    print("Geometry type:", layer_info.get("geometryType"))

    spatial_reference = (
        layer_info
        .get("extent", {})
        .get("spatialReference")
    )

    print("Spatial reference:", spatial_reference)

    print(
        "Max record count:",
        layer_info.get("maxRecordCount"),
    )

    print(
        "Supports pagination:",
        layer_info
        .get("advancedQueryCapabilities", {})
        .get("supportsPagination")
    )


def print_parcel_summary(data: dict) -> None:
    """Print a compact summary of returned parcels."""

    features = data.get("features", [])

    print("\n--- PARCEL RESULTS ---")

    print("Features returned:", len(features))

    for feature in features:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        print(
            f"{properties.get('PARCELID')} | "
            f"{properties.get('SITEADDRESS')} | "
            f"{properties.get('ASSACRES')}"
        )

        print(
            f"    Geometry: {geometry.get('type')}"
        )


def print_parcel_details(data: dict) -> None:
    """Print all attributes for the first returned parcel."""

    features = data.get("features", [])

    if not features:
        print("\nNo parcels returned.")
        return

    feature = features[0]

    print("\n--- FIRST PARCEL ---")

    print("\nProperties:")

    for key, value in feature.get("properties", {}).items():
        print(f"  {key}: {value}")

    print("\nGeometry:")

    geometry = feature.get("geometry", {})

    print("  Type:", geometry.get("type"))

    coordinates = geometry.get("coordinates")

    if coordinates:
        try:
            first_coordinate = coordinates[0][0]
            print("  First coordinate:", first_coordinate)
        except (IndexError, TypeError):
            print("  First coordinate: unavailable")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # -------------------------------------------------------
    # 1. Inspect the GIS layer
    # -------------------------------------------------------

    layer_info = get_layer_info()

    print_layer_info(layer_info)

    # -------------------------------------------------------
    # 2. Query parcels
    # -------------------------------------------------------

    data = fetch_parcels(
        where="1=1",
        limit=10,
    )

    # -------------------------------------------------------
    # 3. Print results
    # -------------------------------------------------------

    print_parcel_summary(data)

    # -------------------------------------------------------
    # 4. Inspect first parcel
    # -------------------------------------------------------

    print_parcel_details(data)