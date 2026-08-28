from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="McAlister Atlas API",
    description="Backend API for the McAlister Atlas geospatial analytics project.",
    version="0.1.0",
)

app.include_router(router)