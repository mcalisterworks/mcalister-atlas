import requests


BASE_URL = (
    "https://gis.gtcountymi.gov/"
    "arcgis/rest/services/Public_Services/"
    "Tax_Parcel_Public/MapServer/0/query"
)


def fetch_parcels(where: str = "1=1", limit: int = 10) -> dict:
    params = {
        "where": where,
        "outFields": "*",
        "returnGeometry": "true",
        "resultRecordCount": limit,
        "f": "geojson",
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    data = fetch_parcels(limit=10)

    print("Features returned:", len(data["features"]))

    for feature in data["features"]:
        props = feature["properties"]

        print(
            props["PARCELID"],
            "|",
            props["SITEADDRESS"],
            "|",
            props["ASSACRES"],
        )