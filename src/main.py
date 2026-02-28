"""Zoom AI Meeting Bot — API Gateway."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.webhooks import router as webhooks_router
from src.admin import router as admin_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown."""
    logger.info("Instruction Bot API starting")
    yield
    logger.info("Instruction Bot API shutting down")


app = FastAPI(
    title="Zoom AI Meeting Bot",
    description="Instruction Bot — joins whitelisted Zoom meetings, records, transcribes, summarizes",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return {
        "service": "Zoom AI Meeting Bot (Instruction Bot)",
        "docs": "/docs",
        "webhook": "/webhooks/zoom",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
