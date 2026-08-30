import os

from dotenv import load_dotenv

import psycopg
import requests
from psycopg.types.json import Json


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

SOURCE = "Grand Traverse County Tax Parcel GIS"

SOURCE_URL = (
    "https://gis.gtcountymi.gov/"
    "arcgis/rest/services/Public_Services/"
    "Tax_Parcel_Public/MapServer/0"
)

# Keep this small while developing.
# We will add pagination later.
RESULT_RECORD_COUNT = 10


# ---------------------------------------------------------------------------
# ArcGIS
# ---------------------------------------------------------------------------

def fetch_parcels():
    """Fetch parcel records from the Grand Traverse County GIS service."""

    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": 4326,
        "f": "geojson",
        "resultRecordCount": RESULT_RECORD_COUNT,
    }

    print("Fetching Grand Traverse County parcels...")

    response = requests.get(
        SOURCE_URL + "/query",
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    features = data.get("features", [])

    print(f"Features returned: {len(features)}")

    return features


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def insert_parcel(cur, feature):
    """Insert one ArcGIS parcel feature into the raw table."""

    p = feature["properties"]
    geometry = feature.get("geometry")

    parcel_id = p.get("PARCELID")

    if not parcel_id:
        raise ValueError("Feature is missing PARCELID")

    cur.execute(
        """
        INSERT INTO raw.grand_traverse_parcels (
            objectid,
            parcelid,
            lowparcelid,
            siteaddress,
            sitectstzp,
            ownernme1,
            ownernme2,
            pstladdress,
            pstlcity,
            pstlstate,
            pstlzip5,
            pstlzip4,
            building,
            unit,
            cvttxdscrp,
            cvttxcd,
            schldscrp,
            schltxcd,
            pre,
            statedarea,
            assacres,
            usecd,
            usedscrp,
            nghbrhdcd,
            classcd,
            classdscrp,
            cnvyname,
            floorcount,
            bldgarea,
            resflrarea,
            resyrblt,
            resstrtyp,
            strclass,
            classmod,
            lndvalue,
            impvalue,
            prvassdval,
            cntassdval,
            assdvalyrcg,
            assdpcntcg,
            prvtxblval,
            cnttxblval,
            txblvalyrchg,
            txblpcntchg,
            prvwnttxod,
            prvsmrtxod,
            totprvtxtod,
            cntwnttxod,
            cntsmrtxod,
            totcnttxod,
            txodyrchg,
            txodpcntchg,
            waterserv,
            sewerserv,
            primezone,
            prprtydscrp,
            lglstartdt,
            lastupdate,
            lasteditor,
            fulpstladdress,
            globalid,
            pnum,

            source,
            source_url,
            source_record_id,

            geom
        )
        VALUES (
            %(OBJECTID)s,
            %(PARCELID)s,
            %(LOWPARCELID)s,
            %(SITEADDRESS)s,
            %(SITECTSTZP)s,
            %(OWNERNME1)s,
            %(OWNERNME2)s,
            %(PSTLADDRESS)s,
            %(PSTLCITY)s,
            %(PSTLSTATE)s,
            %(PSTLZIP5)s,
            %(PSTLZIP4)s,
            %(BUILDING)s,
            %(UNIT)s,
            %(CVTTXDSCRP)s,
            %(CVTTXCD)s,
            %(SCHLDSCRP)s,
            %(SCHLTXCD)s,
            %(PRE)s,
            %(STATEDAREA)s,
            %(ASSACRES)s,
            %(USECD)s,
            %(USEDSCRP)s,
            %(NGHBRHDCD)s,
            %(CLASSCD)s,
            %(CLASSDSCRP)s,
            %(CNVYNAME)s,
            %(FLOORCOUNT)s,
            %(BLDGAREA)s,
            %(RESFLRAREA)s,
            %(RESYRBLT)s,
            %(RESSTRTYP)s,
            %(STRCLASS)s,
            %(CLASSMOD)s,
            %(LNDVALUE)s,
            %(IMPVALUE)s,
            %(PRVASSDVAL)s,
            %(CNTASSDVAL)s,
            %(ASSDVALYRCG)s,
            %(ASSDPCNTCG)s,
            %(PRVTXBLVAL)s,
            %(CNTTXBLVAL)s,
            %(TXBLVALYRCHG)s,
            %(TXBLPCNTCHG)s,
            %(PRVWNTTXOD)s,
            %(PRVSMRTXOD)s,
            %(TOTPRVTXTOD)s,
            %(CNTWNTTXOD)s,
            %(CNTSMRTXOD)s,
            %(TOTCNTTXOD)s,
            %(TXODYRCHG)s,
            %(TXODPCNTCHG)s,
            %(WATERSERV)s,
            %(SEWERSERV)s,
            %(PRIMEZONE)s,
            %(PRPRTYDSCRP)s,
            %(LGLSTARTDT)s,
            %(LASTUPDATE)s,
            %(LASTEDITOR)s,
            %(FULPSTLADDRESS)s,
            %(GlobalID)s,
            %(pnum)s,

            %(source)s,
            %(source_url)s,
            %(source_record_id)s,

            ST_SetSRID(
                ST_Multi(
                    ST_GeomFromGeoJSON(%(geometry)s)
                ),
                4326
            )
        )
        ON CONFLICT (source, source_record_id)
        DO NOTHING
        """,
        {
            **p,
            "source": SOURCE,
            "source_url": SOURCE_URL,
            "source_record_id": parcel_id,
            "geometry": Json(geometry),
        },
    )

    if cur.rowcount == 1:
        print(f"Inserted: {parcel_id}")
    else:
        print(f"Skipped (already exists): {parcel_id}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():

    features = fetch_parcels()

    with psycopg.connect(
        host=DATABASE_HOST,
        port=DATABASE_PORT,
        dbname=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
    ) as conn:

        with conn.cursor() as cur:

            for feature in features:
                insert_parcel(cur, feature)

    print()
    print("Ingest complete.")


if __name__ == "__main__":
    main()