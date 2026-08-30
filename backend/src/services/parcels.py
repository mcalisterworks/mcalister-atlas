from db import get_connection


def get_parcels_by_bbox(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
):
    """
    Return parcels intersecting a bounding box as GeoJSON.
    """

    sql = """
        SELECT
            parcel_id,
            county,
            site_address,
            ST_AsGeoJSON(geometry)::json AS geometry,
            parcel_acres,
            acreage_bucket,
            class_code,
            class_description,
            is_residential,
            is_commercial,
            is_agricultural,
            is_industrial,
            land_value,
            improvement_value,
            assessed_value,
            taxable_value,
            land_value_per_acre,
            assessed_value_per_acre,
            improvement_to_land_ratio,
            taxable_to_assessed_ratio
        FROM analytics.parcel_metrics
        WHERE geometry && ST_MakeEnvelope(
            %s, %s, %s, %s, 4326
        )
        AND ST_Intersects(
            geometry,
            ST_MakeEnvelope(%s, %s, %s, %s, 4326)
        );
    """

    bbox = (min_lon, min_lat, max_lon, max_lat)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, bbox + bbox)

            columns = [column.name for column in cur.description]
            rows = cur.fetchall()

    features = []

    for row in rows:
        record = dict(zip(columns, row))
        geometry = record.pop("geometry")

        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": record,
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def get_parcel(parcel_id: str):
    """
    Return a single parcel and its attributes.
    """

    sql = """
        SELECT
            parcel_id,
            county,
            site_address,
            ST_AsGeoJSON(geometry)::json AS geometry,
            parcel_acres,
            acreage_bucket,
            class_code,
            class_description,
            is_residential,
            is_commercial,
            is_agricultural,
            is_industrial,
            land_value,
            improvement_value,
            assessed_value,
            taxable_value,
            land_value_per_acre,
            assessed_value_per_acre,
            improvement_to_land_ratio,
            taxable_to_assessed_ratio,
            source,
            source_record_count
        FROM analytics.parcel_metrics
        WHERE parcel_id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (parcel_id,))

            row = cur.fetchone()

            if row is None:
                return None

            columns = [column.name for column in cur.description]
            record = dict(zip(columns, row))

    geometry = record.pop("geometry")

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": record,
    }