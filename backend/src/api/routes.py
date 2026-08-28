from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root():
    return {"message": "McAlister Atlas API"}


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.get("/api/v1/properties")
def get_properties():
    return {
        "properties": [
            {
                "id": "demo-001",
                "name": "Demo Property",
                "latitude": 45.123,
                "longitude": -85.456,
            }
        ]
    }


@router.get("/api/v1/properties/{property_id}")
def get_property(property_id: str):
    return {
        "id": property_id,
        "name": "Demo Property",
        "latitude": 45.123,
        "longitude": -85.456,
    }

