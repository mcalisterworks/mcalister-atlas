import httpx


USGS_EPQS_URL = "https://epqs.nationalmap.gov/v1/json"


async def get_elevation(latitude: float, longitude: float) -> float:
    """
    Query the USGS Elevation Point Query Service (EPQS).

    Returns elevation in meters.
    """

    params = {
        "x": longitude,
        "y": latitude,
        "units": "Meters",
        "output": "json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            USGS_EPQS_URL,
            params=params,
        )

        print("USGS status:", response.status_code)
        print("USGS content-type:", response.headers.get("content-type"))
        print("USGS URL:", response.url)
        print("USGS response:", response.text[:1000])

        response.raise_for_status()

        data = response.json()

    return float(data["value"])
