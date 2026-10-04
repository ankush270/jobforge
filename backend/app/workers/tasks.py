"""Background tasks executed by Celery workers."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import select

from app.db.engine import async_session_factory
from app.db.models import Application, Company, FollowUp, Job, Resume, StatusChange, TailoredResume
from app.services.scraper.ghost_detector import analyze_ghost_and_repost
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async function from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.tasks.scrape_all_sources")
def scrape_all_sources():
    """Periodic task: scrape jobs from configured platforms and save to DB."""
    async def _async_scrape():
        from app.services.scraper.engine import scrape_jobs, scan_target_ats_boards

        logger.info("Starting scheduled job scrape in Celery worker (0-1 yr India Tech)")
        # 1. Direct Target ATS Boards scan (Greenhouse, Ashby, Lever - zero-block, high speed)
        # Scans ALL companies from target_companies.json without skipping any company
        ats_jobs = await scan_target_ats_boards(filter_entry_india=True, max_companies=None)

        # 2. Aggregators scan with in-flight 0-1 yr India filter
        aggregator_jobs = await scrape_jobs(
            search_query="software engineer",
            platforms=["linkedin", "indeed"],
            location="India",
            results_wanted=30,
            filter_entry_india=True,
        )

        scraped = ats_jobs + aggregator_jobs
        logger.info(f"Scraped {len(scraped)} total filtered jobs (ATS: {len(ats_jobs)}, Aggregators: {len(aggregator_jobs)})")

        saved = 0
        async with async_session_factory() as session:
            try:
                for item in scraped:
                    key = item["canonical_key"]
                    # Check if already in DB
                    exists = (await session.execute(select(Job.id).where(Job.canonical_key == key))).first()
                    if exists:
                        continue

                    # Upsert company
                    slug = item["company_slug"] or "unknown"
                    comp = (await session.execute(select(Company).where(Company.slug == slug))).scalar_one_or_none()
                    if not comp:
                        comp = Company(name=item["company_name"], slug=slug)
                        session.add(comp)
                        await session.flush()

                    def clean(v):
                        return None if v in (None, "", "nan", "None") else v

                    # Ghost & repost evaluation
                    ghost_eval = await analyze_ghost_and_repost(
                        job_title=item["title"],
                        job_description=clean(item["description"]) or "",
                        company_id=comp.id,
                        posted_at=item.get("posted_at"),
                        source_url=clean(item.get("source_url")),
                        db=session,
                    )

                    new_job = Job(
                        company_id=comp.id,
                        canonical_key=key,
                        title=item["title"],
                        description=clean(item["description"]) or "",
                        location=clean(item.get("location")),
                        salary_min=item.get("salary_min"),
                        salary_max=item.get("salary_max"),
                        salary_currency=clean(item.get("salary_currency")) or "INR",
                        job_type=clean(item.get("job_type")),
                        remote_type="remote" if item.get("is_remote") else None,
                        source_platform=item.get("source_platform", "scraper"),
                        source_url=clean(item.get("source_url")),
                        posted_at=item.get("posted_at"),
                        is_ghost=ghost_eval["is_ghost"],
                        ghost_signals=ghost_eval["ghost_signals"],
                        repost_of=ghost_eval["repost_of"],
                    )
                    session.add(new_job)
                    saved += 1

                await session.commit()
                logger.info(f"Scheduled scrape complete: saved {saved} new jobs")
                return {"scraped": len(scraped), "saved": saved}
            except Exception as e:
                await session.rollback()
                logger.error(f"Error in scrape_all_sources DB save: {e}")
                raise

    return _run_async(_async_scrape())


@celery_app.task(name="app.workers.tasks.check_pending_follow_ups")
def check_pending_follow_ups():
    """Hourly task: check for follow-ups that need to be sent."""
    async def _async_check():
        now = datetime.now(timezone.utc)
        async with async_session_factory() as session:
            try:
                result = await session.execute(
                    select(FollowUp).where(
                        FollowUp.status == "pending",
                        FollowUp.scheduled_at <= now,
                    )
                )
                due_followups = result.scalars().all()
                logger.info(f"Found {len(due_followups)} pending follow-ups due today")
                return {"checked": len(due_followups), "due_ids": [str(f.id) for f in due_followups]}
            except Exception as e:
                logger.error(f"Error checking follow-ups: {e}")
                return {"checked": 0, "error": str(e)}

    return _run_async(_async_check())


@celery_app.task(name="app.workers.tasks.detect_ghosted_applications")
def detect_ghosted_applications():
    """Daily task: mark applications as ghosted after 21 days with no response."""
    async def _async_ghost():
        now = datetime.now(timezone.utc)
        threshold_date = now - timedelta(days=21)
        ghosted_count = 0

        async with async_session_factory() as session:
            try:
                # Select applications in "applied" status for > 21 days
                result = await session.execute(
                    select(Application).where(
                        Application.status == "applied",
                        Application.applied_at <= threshold_date,
                    )
                )
                stale_apps = result.scalars().all()

                for app in stale_apps:
                    app.status = "ghosted"
                    change = StatusChange(
                        application_id=app.id,
                        from_status="applied",
                        to_status="ghosted",
                        notes="Auto-flagged as ghosted after 21 days of employer silence",
                    )
                    session.add(change)
                    ghosted_count += 1

                await session.commit()
                logger.info(f"Detected and marked {ghosted_count} applications as ghosted")
                return {"ghosted": ghosted_count}
            except Exception as e:
                await session.rollback()
                logger.error(f"Error in detect_ghosted_applications: {e}")
                return {"ghosted": 0, "error": str(e)}

    return _run_async(_async_ghost())


@celery_app.task(name="app.workers.tasks.tailor_resume_async")
def tailor_resume_async(user_id: str, resume_id: str, job_id: str):
    """Async resume tailoring with STAR pipeline & anti-hallucination guard."""
    async def _async_tailor():
        from app.services.intelligence.ats_scorer import extract_keywords_from_jd
        from app.services.intelligence.tailor import tailor_resume_pipeline

        u_id = UUID(user_id)
        r_id = UUID(resume_id)
        j_id = UUID(job_id)

        async with async_session_factory() as session:
            try:
                resume = (await session.execute(select(Resume).where(Resume.id == r_id, Resume.user_id == u_id))).scalar_one_or_none()
                if not resume:
                    return {"status": "error", "message": "Resume not found"}

                job = (await session.execute(select(Job).where(Job.id == j_id))).scalar_one_or_none()
                if not job:
                    return {"status": "error", "message": "Job not found"}

                job_keywords = job.keywords
                if not job_keywords or not job_keywords.get("required_skills"):
                    job_keywords = extract_keywords_from_jd(job.description)
                    job.keywords = job_keywords

                # Execute AI STAR tailoring pipeline
                res = await tailor_resume_pipeline(
                    master_resume_content=resume.content,
                    job_description=job.description,
                    job_keywords=job_keywords,
                )

                tailored = TailoredResume(
                    user_id=u_id,
                    source_resume_id=r_id,
                    job_id=j_id,
                    content=res["content"],
                    content_md=res["content_md"],
                    ats_score=res["ats_score"],
                    ats_breakdown=res["ats_breakdown"],
                    missing_keywords=res["missing_keywords"],
                    injectable_keywords=res["injectable_keywords"],
                    recommendations=res["recommendations"],
                    fact_check_status=res["fact_check_status"],
                )
                session.add(tailored)
                await session.commit()
                return {
                    "status": "completed",
                    "tailored_id": str(tailored.id),
                    "ats_score": res["ats_score"],
                    "fact_check_status": res["fact_check_status"],
                }
            except Exception as e:
                await session.rollback()
                logger.error(f"Error in tailor_resume_async: {e}")
                return {"status": "error", "error": str(e)}

    return _run_async(_async_tailor())
