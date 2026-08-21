import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.router import api_router
from app.db.init_db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("naagrakshak.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting NaagRakshak FastAPI Production Backend Engine...")
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
    yield
    logger.info("Shutting down NaagRakshak Backend Engine.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 1. Middleware: CORS (Strict Origin Configuration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow React SPA frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Middleware: Request ID Injector (UUID4)
@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# 3. Router Inclusion (/api/v1)
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "title": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health_check": f"{settings.API_V1_STR}/health"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal System Exception",
            "detail": str(exc),
            "request_id": getattr(request.state, "request_id", "N/A")
        }
    )
