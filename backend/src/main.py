from fastapi import FastAPI

from api.routes import router


app = FastAPI(
    title="Northern Michigan Real Estate API",
    version="0.1.0",
)


app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "Northern Michigan Real Estate API",
        "status": "ok",
    }