from fastapi import APIRouter, HTTPException, Query

from .services.elevation import get_elevation


router = APIRouter(
    prefix="/api/v1",
    tags=["geospatial"],
)


@router.get("/elevation")
async def elevation(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    """
    Return USGS 3DEP elevation for a latitude/longitude.
    """

    try:
        elevation_m = await get_elevation(
            latitude=latitude,
            longitude=longitude,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"USGS elevation service error: {exc}",
        )

    return {
        "latitude": latitude,
        "longitude": longitude,
        "elevation_m": elevation_m,
    }