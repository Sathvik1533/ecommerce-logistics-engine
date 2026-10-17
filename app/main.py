import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.features.inventory import inventory_router
from app.features.orders import orders_router

logger = logging.getLogger("ecommerce_logistics_engine")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for application startup and graceful shutdown."""
    logger.info("Initializing %s in %s mode...", settings.PROJECT_NAME, settings.ENVIRONMENT)
    yield
    logger.info("Shutting down %s...", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Scalable, modular backend engine for global order fulfillment "
        "and transactional inventory reservations."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 Router Registration (Vertical Slices)
api_v1_router = APIRouter(prefix=settings.API_V1_STR)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(inventory_router)
app.include_router(api_v1_router)


@app.get(
    "/health",
    tags=["Observability"],
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Returns HTTP 200 if the application process is running and responding.",
)
def liveness_check(
    current_settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    return {
        "status": "healthy",
        "service": current_settings.PROJECT_NAME,
        "environment": current_settings.ENVIRONMENT,
    }


@app.get(
    "/ready",
    tags=["Observability"],
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Verifies downstream dependencies (database connection) are accessible.",
)
def readiness_check(
    current_settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    checks: dict[str, str] = {"app": "ok"}
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        checks["database"] = "ok"
        return {"status": "ready", "checks": checks}
    except Exception as exc:
        checks["database"] = f"unreachable: {exc!s}"
        return {"status": "degraded", "checks": checks}
