"""Hacker News 'Who is hiring?' Scanner.

Adapts logic from:
- 01_job_scraping_engine/scan-hn.mjs (7KB)
- 01_job_scraping_engine/providers/hackernews.mjs

Fetches high-signal, direct-from-founder/engineering-team tech job postings
from Hacker News' monthly 'Ask HN: Who is hiring?' threads via official Firebase API.
"""

from __future__ import annotations

import html
import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.services.scraper.dedup import generate_canonical_key, slugify

logger = logging.getLogger(__name__)

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


def _clean_html(raw_html: str) -> str:
    """Convert Hacker News comment HTML to clean readable text."""
    if not raw_html:
        return ""
    text = raw_html.replace("<p>", "\n\n").replace("</p>", "")
    text = re.sub(r"<a\s+href=\"([^\"]+)\"[^>]*>.*?</a>", r" \1 ", text)
    text = re.sub(r"<pre><code>(.*?)</code></pre>", r"\n```\n\1\n```\n", text, flags=re.DOTALL)
    text = re.sub(r"<.*?>", "", text)
    return html.unescape(text).strip()


async def scan_hacker_news_hiring(
    search_query: str = "",
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Scan latest 'Ask HN: Who is hiring?' thread on Hacker News."""
    jobs: list[dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 1. Fetch user 'whoishiring' submitted stories
            user_resp = await client.get(f"{HN_API_BASE}/user/whoishiring.json")
            if user_resp.status_code != 200:
                logger.warning(f"HN user fetch returned status {user_resp.status_code}")
                return []

            submitted = user_resp.json().get("submitted", [])
            target_story_id = None

            # Check recent 5 submissions for 'Ask HN: Who is hiring?'
            for sid in submitted[:6]:
                story_resp = await client.get(f"{HN_API_BASE}/item/{sid}.json")
                if story_resp.status_code == 200:
                    story_data = story_resp.json()
                    title = story_data.get("title", "")
                    if "who is hiring?" in title.lower():
                        target_story_id = sid
                        break

            if not target_story_id:
                logger.warning("No active 'Ask HN: Who is hiring?' thread found")
                return []

            # 2. Fetch the thread comments
            thread_resp = await client.get(f"{HN_API_BASE}/item/{target_story_id}.json")
            if thread_resp.status_code != 200:
                return []

            kids = thread_resp.json().get("kids", [])
            query_lower = search_query.strip().lower() if search_query else ""

            # Check up to 50 top comments
            fetch_count = min(len(kids), 60)
            target_kids = kids[:fetch_count]

            for cid in target_kids:
                if len(jobs) >= limit:
                    break

                c_resp = await client.get(f"{HN_API_BASE}/item/{cid}.json")
                if c_resp.status_code != 200:
                    continue

                c_data = c_resp.json()
                if not c_data or c_data.get("deleted") or c_data.get("dead"):
                    continue

                raw_text = c_data.get("text", "")
                if not raw_text:
                    continue

                clean_text = _clean_html(raw_text)

                # Filter by keyword if provided
                if query_lower and query_lower not in clean_text.lower():
                    continue

                # The first line of HN hiring comments follows: "Company | Role | Location | ..."
                first_line = clean_text.split("\n")[0].strip()
                tokens = [t.strip() for t in first_line.split("|")]

                company_name = tokens[0] if len(tokens) > 0 and len(tokens[0]) < 60 else "HN Startup"
                role_title = tokens[1] if len(tokens) > 1 and len(tokens[1]) < 80 else (search_query.title() or "Software Engineer")
                location_str = tokens[2] if len(tokens) > 2 else "Remote / Flexible"

                is_remote = "remote" in clean_text.lower() or "remote" in location_str.lower()
                canonical_key = generate_canonical_key(
                    company_name,
                    role_title,
                    f"https://news.ycombinator.com/item?id={cid}",
                )

                created_time = None
                if c_data.get("time"):
                    created_time = datetime.fromtimestamp(c_data["time"], tz=timezone.utc)

                jobs.append({
                    "canonical_key": canonical_key,
                    "company_name": company_name,
                    "company_slug": slugify(company_name) or "hn-startup",
                    "title": role_title,
                    "description": clean_text,
                    "location": location_str,
                    "salary_min": None,
                    "salary_max": None,
                    "salary_currency": "USD",
                    "job_type": "full-time",
                    "is_remote": is_remote,
                    "source_platform": "hacker_news",
                    "source_url": f"https://news.ycombinator.com/item?id={cid}",
                    "posted_at": created_time or datetime.now(timezone.utc),
                })

    except Exception as e:
        logger.error(f"Error scanning Hacker News hiring thread: {e}")

    logger.info(f"HN Scanner extracted {len(jobs)} jobs for query '{search_query}'")
    return jobs
