from fastapi import FastAPI

app = FastAPI(
    title="McAlister Atlas API",
    description="Backend API for the McAlister Atlas geospatial analytics project.",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"message": "McAlister Atlas API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

