import uvicorn
from fastapi import FastAPI
from api.endpoints.simulator_service import simulator_router
from fastapi.staticfiles import StaticFiles
from pathlib import Path

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "api" / "endpoints" / "simulator_service" / "static"

app = FastAPI(
    title="MMU Simulator API",
    description="API for the MMU/TLB Simulator",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(simulator_router, tags=["Home"])
# app.include_router(about,  tags=["About"])

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True 
    )