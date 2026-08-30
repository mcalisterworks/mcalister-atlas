import os
import json
import psycopg
import requests
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

DATABASE_HOST = os.getenv("POSTGRES_HOST", "localhost")
DATABASE_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DATABASE_NAME = os.getenv("POSTGRES_DB", "mcalister_atlas")
DATABASE_USER = os.getenv("POSTGRES_USER", "postgres")
DATABASE_PASSWORD = os.getenv("POSTGRES_PASSWORD")

if not DATABASE_PASSWORD:
    raise RuntimeError(
        "POSTGRES_PASSWORD is not set. Check your .env file."
    )


SOURCE_URL = (
    "https://gis.gtcountymi.gov/"
    "arcgis/rest/services/Public_Services/"
    "Tax_Parcel_Public/MapServer/0"
)

SOURCE_NAME = "grand_traverse_tax_parcel_public"

# ---------------------------------------------------------------------------
# Testing:
#   10   = small test batches
#   1000 = full ArcGIS batch size
# ---------------------------------------------------------------------------

BATCH_SIZE = 1000


# ---------------------------------------------------------------------------
# ArcGIS
# ---------------------------------------------------------------------------

def fetch_parcel_batches():
    """
    Fetch Grand Traverse County parcels from ArcGIS in batches.

    The ArcGIS service supports pagination and has a maximum
    record count of 1,000 per request.
    """

    offset = 0

    while True:

        params = {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": 4326,
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": BATCH_SIZE,
            "orderByFields": "OBJECTID ASC",
        }

        print(
            f"Fetching records "
            f"{offset + 1:,}-{offset + BATCH_SIZE:,}..."
        )

        response = requests.get(
            SOURCE_URL + "/query",
            params=params,
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise RuntimeError(data["error"])

        features = data.get("features", [])

        print(f"  Received: {len(features):,}")

        if not features:
            break

        yield features

        if len(features) < BATCH_SIZE:
            break

        offset += BATCH_SIZE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_property(properties, field):
    """Safely retrieve an ArcGIS property."""
    return properties.get(field)


# ---------------------------------------------------------------------------
# PostgreSQL / PostGIS
# ---------------------------------------------------------------------------

def insert_parcel(cur, feature):
    """
    Insert one ArcGIS parcel feature into the raw schema.

    Returns:
        True  = row inserted
        False = row skipped because it already exists
    """

    properties = feature["properties"]
    geometry = json.dumps(feature.get("geometry"))

    # -----------------------------------------------------------------------
    # Parcel fields
    # -----------------------------------------------------------------------

    columns = [
        "objectid",
        "parcelid",
        "lowparcelid",
        "siteaddress",
        "sitectstzp",
        "ownernme1",
        "ownernme2",
        "pstladdress",
        "pstlcity",
        "pstlstate",
        "pstlzip5",
        "pstlzip4",
        "building",
        "unit",
        "cvttxdscrp",
        "cvttxcd",
        "schldscrp",
        "schltxcd",
        "pre",
        "statedarea",
        "assacres",
        "usecd",
        "usedscrp",
        "nghbrhdcd",
        "classcd",
        "classdscrp",
        "cnvyname",
        "floorcount",
        "bldgarea",
        "resflrarea",
        "resyrblt",
        "resstrtyp",
        "strclass",
        "classmod",
        "lndvalue",
        "impvalue",
        "prvassdval",
        "cntassdval",
        "assdvalyrcg",
        "assdpcntcg",
        "prvtxblval",
        "cnttxblval",
        "txblvalyrchg",
        "txblpcntchg",
        "prvwnttxod",
        "prvsmrtxod",
        "totprvtxtod",
        "cntwnttxod",
        "cntsmrtxod",
        "totcnttxod",
        "txodyrchg",
        "txodpcntchg",
        "waterserv",
        "sewerserv",
        "primezone",
        "prprtydscrp",
        "lglstartdt",
        "lastupdate",
        "lasteditor",
        "fulpstladdress",
        "globalid",
        "pnum",
    ]

    # ArcGIS field names corresponding to the PostgreSQL columns above.
    source_fields = [
        "OBJECTID",
        "PARCELID",
        "LOWPARCELID",
        "SITEADDRESS",
        "SITECTSTZP",
        "OWNERNME1",
        "OWNERNME2",
        "PSTLADDRESS",
        "PSTLCITY",
        "PSTLSTATE",
        "PSTLZIP5",
        "PSTLZIP4",
        "BUILDING",
        "UNIT",
        "CVTTXDSCRP",
        "CVTTXCD",
        "SCHLDSCRP",
        "SCHLTXCD",
        "PRE",
        "STATEDAREA",
        "ASSACRES",
        "USECD",
        "USEDSCRP",
        "NGHBRHDCD",
        "CLASSCD",
        "CLASSDSCRP",
        "CNVYNAME",
        "FLOORCOUNT",
        "BLDGAREA",
        "RESFLRAREA",
        "RESYRBLT",
        "RESSTRTYP",
        "STRCLASS",
        "CLASSMOD",
        "LNDVALUE",
        "IMPVALUE",
        "PRVASSDVAL",
        "CNTASSDVAL",
        "ASSDVALYRCG",
        "ASSDPCNTCG",
        "PRVTXBLVAL",
        "CNTTXBLVAL",
        "TXBLVALYRCHG",
        "TXBLPCNTCHG",
        "PRVWNTTXOD",
        "PRVSMRTXOD",
        "TOTPRVTXTOD",
        "CNTWNTTXOD",
        "CNTSMRTXOD",
        "TOTCNTTXOD",
        "TXODYRCHG",
        "TXODPCNTCHG",
        "WATERSERV",
        "SEWERSERV",
        "PRIMEZONE",
        "PRPRTYDSCRP",
        "LGLSTARTDT",
        "LASTUPDATE",
        "LASTEDITOR",
        "FULPSTLADDRESS",
        "GlobalID",
        "pnum",
    ]

    values = [
        get_property(properties, field)
        for field in source_fields
    ]

    # -----------------------------------------------------------------------
    # Add geometry and provenance fields
    # -----------------------------------------------------------------------

    columns.extend(
        [
            "geom",
            "source",
            "source_url",
            "source_record_id",
        ]
    )

    values.extend(
        [
            geometry,
            SOURCE_NAME,
            SOURCE_URL,
            str(get_property(properties, "OBJECTID")),
        ]
    )

    # -----------------------------------------------------------------------
    # Build placeholders dynamically
    #
    # Geometry gets a special PostGIS expression instead of a plain %s.
    # -----------------------------------------------------------------------

    placeholders = ["%s"] * len(values)

    geometry_index = len(source_fields)

    placeholders[geometry_index] = """
        ST_SetSRID(
            ST_GeomFromGeoJSON(%s),
            4326
        )
    """

    # -----------------------------------------------------------------------
    # Build INSERT statement
    # -----------------------------------------------------------------------

    column_sql = ",\n            ".join(columns)
    placeholder_sql = ",\n            ".join(placeholders)

    sql = f"""
        INSERT INTO raw.grand_traverse_parcels (
            {column_sql}
        )
        VALUES (
            {placeholder_sql}
        )
        ON CONFLICT (source, source_record_id)
        DO NOTHING
    """

    cur.execute(sql, values)

    return cur.rowcount == 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():

    total_inserted = 0
    total_skipped = 0
    batch_number = 0

    print("Starting Grand Traverse County parcel ingestion...")
    print(f"Source: {SOURCE_URL}")
    print(f"Batch size: {BATCH_SIZE}")
    print()

    with psycopg.connect(
        host=DATABASE_HOST,
        port=DATABASE_PORT,
        dbname=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
    ) as conn:

        with conn.cursor() as cur:

            for features in fetch_parcel_batches():

                batch_number += 1

                batch_inserted = 0
                batch_skipped = 0

                for feature in features:

                    if insert_parcel(cur, feature):
                        batch_inserted += 1
                    else:
                        batch_skipped += 1

                conn.commit()

                total_inserted += batch_inserted
                total_skipped += batch_skipped

                print(
                    f"Batch {batch_number}: "
                    f"{batch_inserted:,} inserted, "
                    f"{batch_skipped:,} skipped"
                )

                print(
                    f"Running total: "
                    f"{total_inserted:,} inserted, "
                    f"{total_skipped:,} skipped"
                )

                print()

    print("Ingest complete.")
    print(f"Total inserted: {total_inserted:,}")
    print(f"Total skipped:  {total_skipped:,}")


if __name__ == "__main__":
    main()
