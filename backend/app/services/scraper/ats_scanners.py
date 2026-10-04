"""Direct ATS Portal Scanners (Greenhouse, Lever, Ashby).

Adapts logic from:
- 02_direct_ats_portal_scanner/ats-vendor.mjs
- 02_direct_ats_portal_scanner/scan-ats-full.mjs
- 02_direct_ats_portal_scanner/discover-ats.mjs
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.services.scraper.dedup import generate_canonical_key, slugify

logger = logging.getLogger(__name__)


async def scan_greenhouse_portal(board_token: str) -> list[dict[str, Any]]:
    """Scan a company's Greenhouse job board via its public JSON API.

    Endpoint: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    jobs: list[dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning(f"Greenhouse board {board_token} returned {resp.status_code}")
                return []
            data = resp.json()

        for item in data.get("jobs", []):
            title = item.get("title", "").strip()
            if not title:
                continue

            company_name = board_token.replace("-", " ").title()
            loc_data = item.get("location", {})
            loc_name = loc_data.get("name") if isinstance(loc_data, dict) else None
            job_url = item.get("absolute_url")
            desc = item.get("content", "")

            # Posted date
            posted_at = None
            if item.get("updated_at"):
                try:
                    posted_at = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
                except Exception:
                    posted_at = datetime.now(timezone.utc)

            key = generate_canonical_key(company_name, title)
            jobs.append({
                "canonical_key": key,
                "company_name": company_name,
                "company_slug": slugify(company_name),
                "title": title,
                "description": desc,
                "location": loc_name,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "USD",
                "job_type": "full-time",
                "is_remote": "remote" in (loc_name or "").lower() or "remote" in title.lower(),
                "source_platform": "greenhouse",
                "source_url": job_url,
                "posted_at": posted_at,
            })
    except Exception as e:
        logger.error(f"Error scanning Greenhouse board {board_token}: {e}")

    return jobs


async def scan_lever_portal(company_slug: str) -> list[dict[str, Any]]:
    """Scan a company's Lever job board via its public JSON API.

    Endpoint: https://api.lever.co/v0/postings/{company_slug}?mode=json
    """
    url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
    jobs: list[dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning(f"Lever board {company_slug} returned {resp.status_code}")
                return []
            data = resp.json()

        for item in data:
            title = item.get("text", "").strip()
            if not title:
                continue

            company_name = company_slug.replace("-", " ").title()
            categories = item.get("categories", {})
            loc = categories.get("location")
            job_url = item.get("hostedUrl")
            desc = item.get("descriptionPlain", "") or item.get("description", "")

            posted_at = None
            if item.get("createdAt"):
                try:
                    posted_at = datetime.fromtimestamp(item["createdAt"] / 1000.0, timezone.utc)
                except Exception:
                    posted_at = datetime.now(timezone.utc)

            workplace_type = item.get("workplaceType", "").lower()
            is_remote = workplace_type == "remote" or "remote" in title.lower()

            key = generate_canonical_key(company_name, title)
            jobs.append({
                "canonical_key": key,
                "company_name": company_name,
                "company_slug": slugify(company_name),
                "title": title,
                "description": desc,
                "location": loc,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "USD",
                "job_type": categories.get("commitment", "full-time"),
                "is_remote": is_remote,
                "source_platform": "lever",
                "source_url": job_url,
                "posted_at": posted_at,
            })
    except Exception as e:
        logger.error(f"Error scanning Lever board {company_slug}: {e}")

    return jobs


async def scan_ashby_portal(company_slug: str) -> list[dict[str, Any]]:
    """Scan a company's Ashby job board via its public JSON API.

    Endpoint: https://api.ashbyhq.com/posting-api/job-board/{company_slug}
    """
    url = f"https://api.ashbyhq.com/posting-api/job-board/{company_slug}"
    jobs: list[dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning(f"Ashby board {company_slug} returned {resp.status_code}")
                return []
            data = resp.json()

        for item in data.get("jobs", []):
            title = item.get("title", "").strip()
            if not title:
                continue

            company_name = company_slug.replace("-", " ").title()
            job_url = item.get("jobUrl")
            loc = item.get("location")
            desc = item.get("descriptionPlain", "") or item.get("descriptionHtml", "")

            posted_at = None
            if item.get("publishedAt"):
                try:
                    posted_at = datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                except Exception:
                    posted_at = datetime.now(timezone.utc)

            is_remote = item.get("isRemote", False) or "remote" in title.lower()

            key = generate_canonical_key(company_name, title)
            jobs.append({
                "canonical_key": key,
                "company_name": company_name,
                "company_slug": slugify(company_name),
                "title": title,
                "description": desc,
                "location": loc,
                "salary_min": None,
                "salary_max": None,
                "salary_currency": "USD",
                "job_type": item.get("employmentType", "full-time"),
                "is_remote": is_remote,
                "source_platform": "ashby",
                "source_url": job_url,
                "posted_at": posted_at,
            })
    except Exception as e:
        logger.error(f"Error scanning Ashby board {company_slug}: {e}")

    return jobs


def discover_ats_vendor(url: str) -> dict[str, str | None]:
    """Identify ATS vendor and extract company slug/token from job URL.
    Adapts logic from 02_direct_ats_portal_scanner/ats-vendor.mjs.
    """
    if not url:
        return {"vendor": None, "token": None}

    url_lower = url.lower()

    if "greenhouse.io" in url_lower:
        # e.g. boards.greenhouse.io/company or greenhouse.io/company/jobs/123
        match = re.search(r"greenhouse\.io/(?:embed/job_board/)?([a-zA-Z0-9_-]+)", url_lower)
        return {"vendor": "greenhouse", "token": match.group(1) if match else None}

    if "lever.co" in url_lower:
        # e.g. jobs.lever.co/company
        match = re.search(r"lever\.co/([a-zA-Z0-9_-]+)", url_lower)
        return {"vendor": "lever", "token": match.group(1) if match else None}

    if "ashbyhq.com" in url_lower:
        # e.g. jobs.ashbyhq.com/company
        match = re.search(r"ashbyhq\.com/([a-zA-Z0-9_-]+)", url_lower)
        return {"vendor": "ashby", "token": match.group(1) if match else None}

    if "workable.com" in url_lower:
        match = re.search(r"workable\.com/([a-zA-Z0-9_-]+)", url_lower)
        return {"vendor": "workable", "token": match.group(1) if match else None}

    if "smartrecruiters.com" in url_lower:
        match = re.search(r"smartrecruiters\.com/([a-zA-Z0-9_-]+)", url_lower)
        return {"vendor": "smartrecruiters", "token": match.group(1) if match else None}

    if "myworkdayjobs.com" in url_lower:
        return {"vendor": "workday", "token": None}

    return {"vendor": None, "token": None}


async def check_job_liveness(source_url: str) -> dict[str, Any]:
    """Check if a job posting is still live or expired/taken down.
    Adapts logic from 02_direct_ats_portal_scanner/check-liveness.mjs.
    """
    if not source_url or not source_url.startswith("http"):
        return {"is_alive": True, "status_code": None, "reason": "No valid URL provided"}

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(
                source_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )

            if resp.status_code in (404, 410):
                return {"is_alive": False, "status_code": resp.status_code, "reason": "HTTP 404/410 Job Removed"}

            body_lower = resp.text.lower()
            expired_phrases = [
                "this job has expired",
                "this position has been filled",
                "no longer accepting applications",
                "job posting is no longer active",
                "this role is closed",
                "job not found",
            ]

            for phrase in expired_phrases:
                if phrase in body_lower:
                    return {
                        "is_alive": False,
                        "status_code": resp.status_code,
                        "reason": f"Page contains '{phrase}'"
                    }

            return {"is_alive": True, "status_code": resp.status_code, "reason": "Live and active"}
    except Exception as e:
        logger.warning(f"Liveness check error for {source_url}: {e}")
        return {"is_alive": True, "status_code": None, "reason": f"Connection check skipped: {e}"}

