"""Jobs API: list, search, create, scrape, clip."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.db.models import Company, Job
from app.dependencies import DB, CurrentUser, OptionalUser
from app.schemas import JobClipRequest, JobCreate, JobListResponse, JobRead, JobScrapeRequest
from app.services.scraper.dedup import generate_canonical_key, slugify
from app.services.scraper.ghost_detector import analyze_ghost_and_repost

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _get_or_create_company_slug(name: str) -> str:
    return slugify(name) or name.lower().replace(" ", "-")


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    db: DB,
    user: OptionalUser = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str | None = None,
    platform: str | None = None,
    location: str | None = None,
    is_alive: bool = True,
):
    """List jobs with filters and pagination."""
    query = select(Job).options(joinedload(Job.company))

    if is_alive:
        query = query.where(Job.is_alive == True)  # noqa: E712
    if platform:
        query = query.where(Job.source_platform == platform)
    if location:
        query = query.where(Job.location.ilike(f"%{location}%"))
    if search:
        query = query.where(
            Job.title.ilike(f"%{search}%") | Job.description.ilike(f"%{search}%")
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(Job.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    jobs = result.unique().scalars().all()

    return JobListResponse(
        jobs=[JobRead.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: UUID, db: DB, user: CurrentUser):
    """Get a single job by ID."""
    result = await db.execute(
        select(Job).options(joinedload(Job.company)).where(Job.id == job_id)
    )
    job = result.unique().scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobRead.model_validate(job)


@router.post("/", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(body: JobCreate, db: DB, user: CurrentUser):
    """Manually add a job listing."""
    # Upsert company
    company_slug = _get_or_create_company_slug(body.company_name)
    result = await db.execute(select(Company).where(Company.slug == company_slug))
    company = result.scalar_one_or_none()
    if not company:
        company = Company(name=body.company_name, slug=company_slug)
        db.add(company)
        await db.flush()

    # Generate canonical key for dedup
    canonical_key = generate_canonical_key(body.company_name, body.title)

    # Check for duplicate
    existing = await db.execute(select(Job).where(Job.canonical_key == canonical_key))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Job already exists (duplicate detected)")

    # Analyze for ghost job & repost signals
    ghost_eval = await analyze_ghost_and_repost(
        job_title=body.title,
        job_description=body.description,
        company_id=company.id,
        posted_at=None,
        source_url=body.source_url,
        db=db,
        check_wayback=True,
    )

    job = Job(
        company_id=company.id,
        canonical_key=canonical_key,
        title=body.title,
        description=body.description,
        location=body.location,
        salary_min=body.salary_min,
        salary_max=body.salary_max,
        salary_currency=body.salary_currency,
        job_type=body.job_type,
        remote_type=body.remote_type,
        source_platform=body.source_platform,
        source_url=body.source_url,
        is_ghost=ghost_eval["is_ghost"],
        ghost_signals=ghost_eval["ghost_signals"],
        repost_of=ghost_eval["repost_of"],
    )
    db.add(job)
    await db.flush()

    # Reload with company relationship
    await db.refresh(job, attribute_names=["company"])
    return JobRead.model_validate(job)


@router.post("/clip", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def clip_job(body: JobClipRequest, db: DB, user: CurrentUser):
    """Browser extension: clip a job from any page."""
    create_body = JobCreate(
        title=body.title,
        company_name=body.company_name,
        description=body.description,
        source_url=body.source_url,
        source_platform=body.source_platform,
        location=body.location,
    )
    return await create_job(create_body, db, user)


@router.post("/scrape")
async def scrape_jobs(body: JobScrapeRequest, db: DB, user: CurrentUser):
    """Scrape jobs from the requested platforms and save new ones to the feed."""
    from app.services.scraper.engine import scrape_jobs as run_scraper, scan_target_ats_boards

    results_wanted = max(1, min(body.results_wanted, 50))
    scraped = await run_scraper(
        search_query=body.search_query,
        platforms=body.platforms,
        location=body.location,
        results_wanted=results_wanted,
        filter_entry_india=body.filter_entry_india,
    )

    if body.scan_target_companies:
        target_jobs = await scan_target_ats_boards(
            filter_entry_india=body.filter_entry_india,
            max_companies=None,
        )
        scraped.extend(target_jobs)

    def clean(v: str | None) -> str | None:
        return None if v in (None, "", "nan", "None") else v

    saved = 0
    seen: set[str] = set()
    company_cache: dict[str, Company] = {}

    for item in scraped:
        try:
            key = item.get("canonical_key")
            if not key or key in seen:
                continue
            seen.add(key)

            existing = await db.execute(select(Job.id).where(Job.canonical_key == key))
            if existing.first():
                continue

            comp_name = clean(item.get("company_name")) or "Unknown Company"
            slug = item.get("company_slug") or slugify(comp_name) or "unknown"

            company = company_cache.get(slug)
            if company is None:
                company = (await db.execute(select(Company).where(Company.slug == slug))).scalar_one_or_none()
                if company is None:
                    company = Company(name=comp_name, slug=slug)
                    db.add(company)
                    await db.flush()
                company_cache[slug] = company

            # Fast ghost analysis on scraped jobs (archive.org check reserved for deep 8-block eval)
            ghost_eval = await analyze_ghost_and_repost(
                job_title=item.get("title") or "Untitled Position",
                job_description=clean(item.get("description")) or "",
                company_id=company.id,
                posted_at=item.get("posted_at"),
                source_url=clean(item.get("source_url")),
                db=db,
                check_wayback=False,
            )

            job = Job(
                company_id=company.id,
                canonical_key=key,
                title=item.get("title") or "Untitled Position",
                description=clean(item.get("description")) or "",
                location=clean(item.get("location")),
                salary_min=item.get("salary_min"),
                salary_max=item.get("salary_max"),
                salary_currency=clean(item.get("salary_currency")) or "INR",
                job_type=clean(item.get("job_type")),
                remote_type="remote" if item.get("is_remote") else None,
                source_platform=item.get("source_platform") or "web",
                source_url=clean(item.get("source_url")),
                posted_at=item.get("posted_at"),
                is_ghost=ghost_eval.get("is_ghost", False),
                ghost_signals=ghost_eval.get("ghost_signals", []),
                repost_of=ghost_eval.get("repost_of"),
            )
            db.add(job)
            saved += 1
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Skipping job insertion due to error: {e}")
            continue

    await db.flush()
    return {
        "message": f"Scraped {len(scraped)} jobs, {saved} new saved",
        "scraped": len(scraped),
        "saved": saved,
        "platforms": body.platforms,
        "query": body.search_query,
        "status": "completed",
    }
