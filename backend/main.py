import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Resolve paths from this file, not from the terminal's current directory.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")

# Load backend/.env reliably, even when Uvicorn is started from the project root.
load_dotenv(os.path.join(BASE_DIR, ".env"))

from backend.models import Base, engine
from backend.routers import ALL
from backend.seed import seed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

Base.metadata.create_all(engine)
seed()

app = FastAPI(title="TripMateAi")

for router in ALL:
    app.include_router(router, prefix="/api")


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "service": "TripMateAi API"}


@app.exception_handler(Exception)
async def boom(request: Request, exc: Exception):
    logging.getLogger("TripMateAi").exception("Unhandled error")
    return JSONResponse(
        {"detail": "Something went wrong on our side. Please try again."},
        status_code=500,
    )


app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="web",
)
