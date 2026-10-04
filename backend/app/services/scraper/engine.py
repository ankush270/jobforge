"""Job scraping engine — multi-platform orchestrator.

Uses python-jobspy for LinkedIn, Indeed, Glassdoor, Naukri scraping.
Adapted from career-ops' scan.mjs and ai-job-search's scraper.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.services.scraper.dedup import generate_canonical_key, slugify

logger = logging.getLogger(__name__)


async def scrape_jobs(
    search_query: str,
    platforms: list[str] | None = None,
    location: str | None = None,
    results_wanted: int = 25,
    filter_entry_india: bool = False,
) -> list[dict[str, Any]]:
    """Scrape jobs from multiple platforms.

    Args:
        search_query: Job title or keyword search.
        platforms: List of platforms to scrape. Defaults to LinkedIn + Indeed.
        location: Location filter.
        results_wanted: Max results per platform.
        filter_entry_india: If True, keep only 0-1 yr experience India engineering jobs.

    Returns:
        List of normalized job dicts ready for DB insertion.
    """
    if platforms is None:
        platforms = ["linkedin", "indeed"]

    jobs = []

    # Direct ATS Portal Scanners (Feature #2) & Hacker News (Feature #1)
    from app.services.scraper.ats_scanners import scan_greenhouse_portal, scan_lever_portal, scan_ashby_portal
    from app.services.scraper.hn_scanner import scan_hacker_news_hiring
    from app.services.scraper.filters import is_entry_level_india_engineering

    direct_scanned = False
    ats_direct = [p for p in platforms if p in ("greenhouse", "lever", "ashby")]
    if ats_direct:
        # 1. Try if query itself is a specific company token
        token_candidate = search_query.strip().lower().replace(" ", "-")
        for p in ats_direct:
            try:
                if p == "greenhouse":
                    gh_jobs = await scan_greenhouse_portal(token_candidate)
                    jobs.extend(gh_jobs[:results_wanted])
                elif p == "lever":
                    lev_jobs = await scan_lever_portal(token_candidate)
                    jobs.extend(lev_jobs[:results_wanted])
                elif p == "ashby":
                    ash_jobs = await scan_ashby_portal(token_candidate)
                    jobs.extend(ash_jobs[:results_wanted])
            except Exception:
                pass

        # 2. If query was a job role, scan target companies and filter by query terms
        if len(jobs) < results_wanted:
            ats_target_jobs = await scan_target_ats_boards(
                filter_entry_india=filter_entry_india,
                max_companies=20,
            )
            q_words = [w for w in search_query.lower().split() if len(w) > 2]
            for tj in ats_target_jobs:
                if tj.get("source_platform") in ats_direct:
                    t_title = tj.get("title", "").lower()
                    t_desc = tj.get("description", "").lower()
                    if not q_words or any(w in t_title or w in t_desc for w in q_words):
                        jobs.append(tj)
                        if len(jobs) >= results_wanted:
                            break
        direct_scanned = True

    if "hacker_news" in platforms or "hn" in platforms or "hackernews" in platforms:
        hn_jobs = await scan_hacker_news_hiring(search_query, limit=results_wanted)
        jobs.extend(hn_jobs[:results_wanted])
        direct_scanned = True

    try:
        import asyncio
        from jobspy import scrape_jobs as jobspy_scrape

        # Map our platform names to jobspy's expected format
        site_names = []
        for p in platforms:
            if p in ("linkedin", "indeed", "glassdoor", "zip_recruiter", "google", "bayt", "naukri"):
                site_names.append(p)

        if site_names:
            df = await asyncio.to_thread(
                jobspy_scrape,
                site_name=site_names,
                search_term=search_query,
                location=location or "India",
                results_wanted=results_wanted,
                country_indeed="India",
            )

            for _, row in df.iterrows():
                company = str(row.get("company", "Unknown")).strip()
                title = str(row.get("title", "")).strip()

                if not title:
                    continue

                canonical_key = generate_canonical_key(company, title, str(row.get("job_url", "")))

                job = {
                    "canonical_key": canonical_key,
                    "title": title,
                    "company_name": company,
                    "company_slug": slugify(company) or company.lower().replace(" ", "-"),
                    "description": str(row.get("description", "")),
                    "location": str(row.get("location", "")),
                    "salary_min": _parse_salary(row.get("min_amount")),
                    "salary_max": _parse_salary(row.get("max_amount")),
                    "salary_currency": str(row.get("currency", "INR")),
                    "job_type": str(row.get("job_type", "")),
                    "source_platform": str(row.get("site", platforms[0])),
                    "source_url": str(row.get("job_url", "")),
                    "posted_at": _parse_date(row.get("date_posted")),
                    "is_remote": "remote" in str(row.get("location", "")).lower(),
                }
                jobs.append(job)

            logger.info(f"Scraped {len(jobs)} total jobs (including {site_names})")

    except ImportError:
        logger.warning("python-jobspy not installed. Falling back to direct ATS results.")
    except Exception as e:
        logger.error(f"JobSpy scraping failed: {e}")

    # In-Flight Filter for 0-1 yr India engineering if requested
    if filter_entry_india:
        filtered_jobs = []
        for j in jobs:
            if is_entry_level_india_engineering(
                title=j.get("title", ""),
                location=j.get("location"),
                description=j.get("description", ""),
            ):
                filtered_jobs.append(j)
        jobs = filtered_jobs

    # Deduplicate accumulated jobs by canonical_key
    seen_keys: set[str] = set()
    deduped_jobs: list[dict[str, Any]] = []
    for j in jobs:
        ck = j.get("canonical_key")
        if ck and ck not in seen_keys:
            seen_keys.add(ck)
            deduped_jobs.append(j)

    return deduped_jobs


async def scan_target_ats_boards(
    companies_file: str | None = None,
    filter_entry_india: bool = True,
    max_companies: int | None = None,
) -> list[dict[str, Any]]:
    """Scan all discovered ATS boards (Greenhouse, Ashby, Lever) for target companies.

    Prioritizes target_companies.json so that all tracked target companies with ATS portals
    are scanned without any company being missed.
    Applies in-flight filtering to retain only relevant 0-1 yr India engineering jobs.
    """
    import asyncio
    import json
    from pathlib import Path
    from app.services.scraper.ats_scanners import (
        scan_greenhouse_portal,
        scan_lever_portal,
        scan_ashby_portal,
        discover_ats_vendor,
    )
    from app.services.scraper.filters import is_entry_level_india_engineering

    if companies_file is None:
        candidate_paths = [
            Path("target_companies.json"),
            Path(__file__).resolve().parents[5] / "target_companies.json",
            Path("e:/Projects/job/extracted_features/target_companies.json"),
            Path("discovered_ats_companies.json"),
            Path(__file__).resolve().parents[5] / "discovered_ats_companies.json",
            Path("e:/Projects/job/extracted_features/discovered_ats_companies.json"),
        ]
        for p in candidate_paths:
            if p.exists():
                companies_file = str(p)
                break

    if not companies_file or not Path(companies_file).exists():
        logger.warning("No target companies file found.")
        return []

    with open(companies_file, encoding="utf-8") as f:
        target_list = json.load(f)

    if max_companies is not None and max_companies > 0:
        target_list = target_list[:max_companies]

    all_jobs: list[dict[str, Any]] = []

    async def _scan_one(comp: dict[str, Any]) -> list[dict[str, Any]]:
        comp_name = comp.get("name", "")
        vendor = comp.get("vendor")
        token = comp.get("token")

        # Dynamically discover ATS vendor and token if not pre-populated
        if not vendor or not token:
            url = comp.get("careers_url", "")
            discovered = discover_ats_vendor(url)
            vendor = discovered.get("vendor")
            token = discovered.get("token")

        if not vendor or not token:
            return []

        try:
            res: list[dict[str, Any]] = []
            if vendor == "greenhouse":
                res = await scan_greenhouse_portal(token)
            elif vendor == "lever":
                res = await scan_lever_portal(token)
            elif vendor == "ashby":
                res = await scan_ashby_portal(token)

            # Ensure company_name from target registry is preserved
            if comp_name:
                for j in res:
                    j["company_name"] = comp_name
                    j["company_slug"] = slugify(comp_name)
                    j["canonical_key"] = generate_canonical_key(comp_name, j.get("title", ""), j.get("source_url", ""))
            return res
        except Exception as e:
            logger.warning(f"Error scanning {comp.get('name')}: {e}")
        return []

    # Run in parallel batches of 20 for optimal speed and reliability
    chunk_size = 20
    for i in range(0, len(target_list), chunk_size):
        chunk = target_list[i : i + chunk_size]
        batch_results = await asyncio.gather(*[_scan_one(c) for c in chunk])
        for res in batch_results:
            all_jobs.extend(res)

    # In-flight filter for 0-1 yr India engineering jobs
    filtered: list[dict[str, Any]] = []
    seen: set[str] = set()
    for j in all_jobs:
        key = j.get("canonical_key")
        if not key or key in seen:
            continue
        if filter_entry_india:
            if not is_entry_level_india_engineering(
                title=j.get("title", ""),
                location=j.get("location"),
                description=j.get("description", ""),
            ):
                continue
        seen.add(key)
        filtered.append(j)

    logger.info(f"Target ATS scan complete: {len(filtered)} filtered jobs from {len(target_list)} companies.")
    return filtered



def _parse_salary(value: Any) -> int | None:
    """Parse salary value to integer."""
    if value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def _parse_date(value: Any) -> datetime | None:
    """Parse date to datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    try:
        return datetime.fromisoformat(str(value)).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None
