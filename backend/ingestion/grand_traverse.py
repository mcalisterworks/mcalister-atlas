import requests
from bs4 import BeautifulSoup


BASE_URL = "https://maps.grandtraverse.org/propertydetails.asp"

DEFAULT_PARAMS = {
    "caption": "Parcel",
    "cc": "0",
    "cid": "3",
    "from": "link",
    "indexfield": "parcel_no",
    "type": "string",
}


def fetch_property(parcel_number: str) -> str:
    params = DEFAULT_PARAMS.copy()
    params["pid"] = parcel_number

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    return response.text


def parse_property(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    property_data = {}

    for row in soup.select("tr.PDBrow"):
        cells = row.find_all("td")

        if len(cells) < 2:
            continue

        field = cells[0].get_text(" ", strip=True).rstrip(":")
        value = cells[1].get_text(" ", strip=True)

        property_data[field] = value

    return property_data

def fetch_arcgis_app():
    app_id = "1f27e1d5c8bc4d8ea91e000305a8b6eb"

    url = (
        "https://grand-traverse.maps.arcgis.com/"
        f"sharing/rest/content/items/{app_id}/data"
    )

    response = requests.get(
        url,
        params={"f": "json"},
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    parcel_number = "01-001-001-00"

    html = fetch_property(parcel_number)

    soup = BeautifulSoup(html, "html.parser")

    print("\n--- LINKS ---")

    for link in soup.find_all("a", href=True):
        text = link.get_text(" ", strip=True)
        href = link["href"]
        print(f"{text!r} -> {href}")

    property_data = parse_property(html)

    print("\n--- PROPERTY DATA ---")

    for field, value in property_data.items():
        print(f"{field}: {value}")

    app_data = fetch_arcgis_app()

    print("\n--- ARCGIS APP DATA ---")
    print(app_data)