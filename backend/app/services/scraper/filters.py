"""Smart In-Flight Job Filtering.

Filters scraped jobs before DB insertion based on:
1. Role Relevance (Engineering / Tech only)
2. Experience Level (0-1 yr / Entry / Fresher / Early Career)
3. Location (Strictly India & India-eligible Remote)
"""

from __future__ import annotations

import re
from typing import Any

INDIA_CITIES = [
    "india", "bengaluru", "bangalore", "hyderabad", "pune",
    "gurugram", "gurgaon", "noida", "mumbai", "delhi", "chennai", "kolkata"
]

NON_INDIA_LOCATIONS = [
    "usa", "united states", "us only", "canada", "uk", "london",
    "germany", "berlin", "australia", "japan", "brazil", "singapore", "netherlands", "france"
]

TECH_KEYWORDS = [
    "software", "engineer", "developer", "sde", "frontend", "backend",
    "fullstack", "full stack", "python", "golang", "react", "node", "java",
    "devops", "cloud", "data engineer", "machine learning", "ai", "sdet", "qa"
]

NON_TECH_KEYWORDS = [
    "sales", "marketing", "recruiter", "talent acquisition", "human resources",
    "hr coordinator", "account executive", "business development", "bdr", "sdr",
    "legal", "payroll", "finance manager", "compliance", "accountant",
    "customer success", "customer support", "people partner"
]

SENIOR_PATTERNS = [
    r"\bsenior\b", r"\bsr\.?\b", r"\blead\b", r"\bprincipal\b", r"\bstaff\b",
    r"\barchitect\b", r"\bdirector\b", r"\bvp\b", r"\bvice president\b",
    r"\bhead of\b", r"\bmanager\b", r"\biii\b", r"\biv\b", r"\bv\b"
]

ENTRY_KEYWORDS = [
    "entry", "graduate", "associate", "junior", "jr.", "jr ",
    "sde 1", "sde i", "sde-1", "sde-i", "software engineer 1", "software engineer i",
    "early career", "trainee", "fresher", "intern"
]


def is_entry_level_india_engineering(
    title: str,
    location: str | None = None,
    description: str = "",
) -> bool:
    """Evaluate if a job matches 0-1 Year Experience, India Location, and Engineering Role."""
    t_lower = (title or "").lower()
    loc_lower = (location or "").lower()
    desc_lower = (description or "").lower()

    # 1. Tech & Engineering Check
    if not any(k in t_lower for k in TECH_KEYWORDS):
        return False
    if any(k in t_lower for k in NON_TECH_KEYWORDS):
        return False

    # 2. Seniority Gate (0-1 yr: strictly exclude senior / lead / staff / director)
    if any(re.search(pat, t_lower) for pat in SENIOR_PATTERNS):
        return False

    # Check description for 3+ or 5+ years experience demands
    if desc_lower:
        if re.search(r"\b([3-9]|1\d)\+?\s*years?(?:\s+of)?\s+experience\b", desc_lower):
            return False

    # 3. Location Gate (Strict India or Global Remote)
    has_india = any(c in loc_lower for c in INDIA_CITIES)
    if has_india:
        return True

    # If marked remote, ensure it is NOT explicitly restricted to non-India regions (e.g. Remote USA)
    if "remote" in loc_lower:
        if any(d in loc_lower for d in NON_INDIA_LOCATIONS):
            return False
        return True

    # Discard non-India on-site
    return False
