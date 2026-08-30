from fastapi import APIRouter, HTTPException, Query

from services.parcels import get_parcel, get_parcels_by_bbox


router = APIRouter()


@router.get("/api/parcels")
def parcels(
    bbox: str = Query(
        ...,
        description="Bounding box as min_lon,min_lat,max_lon,max_lat",
    )
):
    """
    Return parcels within a bounding box as GeoJSON.
    """

    try:
        values = [float(value.strip()) for value in bbox.split(",")]

        if len(values) != 4:
            raise ValueError

        min_lon, min_lat, max_lon, max_lat = values

        if min_lon >= max_lon or min_lat >= max_lat:
            raise ValueError

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="bbox must be min_lon,min_lat,max_lon,max_lat",
        )

    return get_parcels_by_bbox(
        min_lon,
        min_lat,
        max_lon,
        max_lat,
    )


@router.get("/api/parcels/{parcel_id}")
def parcel(parcel_id: str):
    """
    Return a single parcel as GeoJSON.
    """

    result = get_parcel(parcel_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Parcel {parcel_id} not found",
        )

    return result