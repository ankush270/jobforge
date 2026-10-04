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

    # In dev, auto-create tables. In prod, use Alembic migrations.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "llm_providers": _get_llm_status(),
    }


def _get_llm_status() -> dict:
    from app.ai.llm_router import get_configured_providers

    return {"configured": get_configured_providers(), "default_model": settings.default_llm_model}
