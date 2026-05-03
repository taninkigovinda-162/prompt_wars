"""
CivicGuide — Smart Election Assistant API.

FastAPI application serving the CivicGuide frontend and AI chat API.
Integrates Google Cloud Run, Gemini AI, Firebase Auth, and Firestore.
"""
import os
import logging
import google.cloud.logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes.routes import router as api_router
from app.utils.config import settings
from app.utils.security import setup_security
from app.services.ai_service import ai_service  # Initialize on startup

# Setup Google Cloud Logging if deployed on Cloud Run
if os.environ.get("K_SERVICE"):
    try:
        client = google.cloud.logging.Client()
        client.setup_logging()
    except Exception as e:
        logging.basicConfig(level=logging.INFO)
        logging.warning(f"Google Cloud Logging not available: {e}")
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Content Security Policy — allows YouTube, Google Slides, Fonts, and Firebase
CSP_POLICY = (
    "default-src 'self'; "
    "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com "
    "https://docs.google.com https://accounts.google.com https://*.google.com; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://www.gstatic.com "
    "https://www.youtube.com https://docs.google.com https://apis.google.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
    "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
    "connect-src 'self' https://*.googleapis.com https://*.firebaseio.com; "
    "img-src 'self' data: https:;"
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

    # Security & CORS
    setup_security(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security Headers Middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = CSP_POLICY
        return response

    # API Routers
    app.include_router(api_router, prefix="")

    # Health Check Endpoint
    @app.get("/health", tags=["System"])
    async def health_check():
        """Return service health status and AI readiness."""
        gemini_ready = ai_service.model is not None
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "ai_service_ready": gemini_ready,
            "ai_mode": "gemini-2.5-flash" if gemini_ready else "fallback",
            "gemini_api_key_set": bool(ai_service._get_api_key()),
        }

    # Mount static files (Frontend) — must be last to avoid shadowing API routes
    frontend_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend"
    )
    if os.path.exists(frontend_path):
        app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
    else:
        logger.warning(f"Frontend directory not found at {frontend_path}")

    return app


app = create_app()
