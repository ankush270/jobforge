"""JobForge — FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.engine import engine
from app.db.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables (dev-only), configure logging."""
    settings.setup_logging()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    # Auto-create tables if not present; gracefully continue if tables exist
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Database table initialization warning (continuing startup): {e}")

    yield

    await engine.dispose()


app = FastAPI(
    title="JobForge API",
    description="AI-powered job search command center — scrape, tailor, apply, track.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────
from app.api.auth import router as auth_router  # noqa: E402
from app.api.resumes import router as resumes_router  # noqa: E402
from app.api.jobs import router as jobs_router  # noqa: E402
from app.api.applications import router as applications_router  # noqa: E402
from app.api.evaluations import router as evaluations_router  # noqa: E402
from app.api.cover_letters import router as cover_letters_router  # noqa: E402
from app.api.interviews import router as interviews_router  # noqa: E402
from app.api.salaries import router as salaries_router  # noqa: E402
from app.api.companies import router as companies_router  # noqa: E402
from app.api.qa_bank import router as qa_bank_router  # noqa: E402
from app.api.contacts import router as contacts_router  # noqa: E402

app.include_router(auth_router, prefix="/api")
app.include_router(resumes_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(applications_router, prefix="/api")
app.include_router(evaluations_router, prefix="/api")
app.include_router(cover_letters_router, prefix="/api")
app.include_router(interviews_router, prefix="/api")
app.include_router(salaries_router, prefix="/api")
app.include_router(companies_router, prefix="/api")
app.include_router(qa_bank_router, prefix="/api")
app.include_router(contacts_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint for pinging and uptime monitors."""
    return {
        "service": "JobForge API",
        "status": "online",
        "version": "0.1.0",
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/health")
@app.get("/api/health")
async def health():
    """Ultra-lightweight keep-alive health route for Render/cron pings (prevents sleep)."""
    from datetime import datetime, timezone
    return {
        "status": "ok",
        "service": "JobForge API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _get_llm_status() -> dict:
    try:
        from app.ai.llm_router import get_configured_providers
        return {"configured": get_configured_providers(), "default_model": settings.default_llm_model}
    except Exception:
        return {"configured": [], "default_model": None}
