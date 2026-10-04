"""Ghost Job & Repost Detector service.

Adapts logic from:
- 14_ghost_job_and_repost_detector/detect-reposts.mjs (40KB)
- 14_ghost_job_and_repost_detector/check-jd-archive.mjs (58KB)
- 14_ghost_job_and_repost_detector/dead-boards.mjs
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Job

logger = logging.getLogger(__name__)

# Minimum days difference for a repost vs concurrent posting
MIN_REPOST_SPAN_DAYS = 1
MAX_REPOST_WINDOW_DAYS = 90
STALE_POSTING_DAYS = 45
WAYBACK_STALE_DAYS = 45


async def check_wayback_history(source_url: str | None) -> dict[str, Any]:
    """Check Wayback Machine (archive.org) for historical snapshots of the job posting URL.
    
    If the exact URL was already indexed 45+ days ago, it provides independent,
    external proof that this opening has been circulating without being filled.
    """
    if not source_url or not (source_url.startswith("http://") or source_url.startswith("https://")):
        return {"has_history": False, "signal": None}

    try:
        async with httpx.AsyncClient(timeout=3.5) as client:
            resp = await client.get(
                f"https://archive.org/wayback/available?url={source_url}",
                headers={"User-Agent": "JobForge/0.1.0"},
            )
            if resp.status_code == 200:
                data = resp.json()
                closest = data.get("archived_snapshots", {}).get("closest")
                if closest and closest.get("available"):
                    ts = closest.get("timestamp", "")
                    if len(ts) >= 8:
                        snapshot_date = datetime.strptime(ts[:8], "%Y%m%d").replace(tzinfo=timezone.utc)
                        now = datetime.now(timezone.utc)
                        days_ago = (now - snapshot_date).days
                        if days_ago >= WAYBACK_STALE_DAYS:
                            return {
                                "has_history": True,
                                "days_ago": days_ago,
                                "first_seen_date": snapshot_date.strftime("%Y-%m-%d"),
                                "snapshot_url": closest.get("url"),
                                "signal": (
                                    f"WAYBACK_GHOST_SIGNAL: Posting URL was first archived {days_ago} days ago "
                                    f"({snapshot_date.strftime('%Y-%m-%d')}) on Wayback Machine"
                                ),
                            }
    except Exception as e:
        logger.debug(f"Wayback Machine API check skipped or timed out: {e}")

    return {"has_history": False, "signal": None}


# Words to ignore when determining title identity
_NOISE_WORDS = frozenset({
    "the", "a", "an", "and", "or", "for", "in", "at", "to", "of", "with",
    "f/m/d", "m/f/d", "w/m/d", "remote", "hybrid", "onsite", "full-time", "part-time",
})


def normalize_title_identity(title: str) -> frozenset[str]:
    """Extract a normalized set of title tokens to prevent merging distinct requisitions.
    Per constraint 2 in detect-reposts.mjs: requires title identity, not fuzzy matching.
    """
    clean = re.sub(r"[^\w\s]", " ", title.lower())
    tokens = [t for t in clean.split() if t not in _NOISE_WORDS and len(t) > 1]
    return frozenset(tokens)


async def analyze_ghost_and_repost(
    job_title: str,
    job_description: str,
    company_id: UUID | None,
    posted_at: datetime | None,
    source_url: str | None,
    db: AsyncSession,
    check_wayback: bool = False,
) -> dict[str, Any]:
    """Analyze a job for ghost posting signals and repost clusters.

    Returns:
        {
            "is_ghost": bool,
            "ghost_signals": list[str],
            "repost_of": UUID | None,
        }
    """
    ghost_signals: list[str] = []
    repost_of: UUID | None = None
    now = datetime.now(timezone.utc)

    # 1. Stale Posting Check (check-jd-archive logic)
    if posted_at:
        # Make sure posted_at is timezone-aware
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        age_days = (now - posted_at).days
        if age_days >= STALE_POSTING_DAYS:
            ghost_signals.append(f"STALE_POSTING: Job posted {age_days} days ago and still listed")

    # 2. Vague / Evergreen Description Check
    desc_words = job_description.split()
    if len(desc_words) < 80:
        ghost_signals.append("EVERGREEN_JD: Extremely short description (< 80 words), common in pipeline harvesting")

    # 3. Repost Detection against database history (detect-reposts.mjs logic)
    if company_id:
        new_title_tokens = normalize_title_identity(job_title)

        # Query recent jobs from the same company within the 90-day window
        result = await db.execute(
            select(Job).where(
                Job.company_id == company_id,
                Job.is_alive == True,
            ).order_by(Job.created_at.desc()).limit(20)
        )
        existing_jobs = result.scalars().all()

        for old_job in existing_jobs:
            # Different URL check
            if source_url and old_job.source_url and source_url == old_job.source_url:
                continue

            old_title_tokens = normalize_title_identity(old_job.title)
            # Check title identity
            if new_title_tokens and new_title_tokens == old_title_tokens:
                # Check span in days
                old_created = old_job.created_at
                if old_created.tzinfo is None:
                    old_created = old_created.replace(tzinfo=timezone.utc)
                span_days = abs((now - old_created).days)

                if MIN_REPOST_SPAN_DAYS <= span_days <= MAX_REPOST_WINDOW_DAYS:
                    repost_of = old_job.id
                    ghost_signals.append(
                        f"REPOST_DETECTED: Re-listed {span_days} days after previous opening ({old_job.title})"
                    )

    # 4. Live Wayback Machine Archival History Check (on deep eval or single clips)
    if check_wayback and source_url:
        wayback_res = await check_wayback_history(source_url)
        if wayback_res.get("has_history") and wayback_res.get("signal"):
            ghost_signals.append(wayback_res["signal"])

    # Determine is_ghost: if 2 or more signals, or explicit repost of stale opening, or wayback history
    is_ghost = (
        len(ghost_signals) >= 2
        or any("REPOST_DETECTED" in s for s in ghost_signals)
        or any("WAYBACK_GHOST_SIGNAL" in s for s in ghost_signals)
    )

    return {
        "is_ghost": is_ghost,
        "ghost_signals": ghost_signals,
        "repost_of": repost_of,
    }
