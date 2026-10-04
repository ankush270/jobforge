"""Job dedup engine — canonical key generation.

Adapted from career-ops' job_key.py. Generates deterministic, collision-free
keys from company+title so the same job on multiple platforms maps to one entry.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

COMPANY_MAX = 40
TITLE_MAX = 60
HASH_LEN = 6

_NON_SLUG = re.compile(r"[^a-z0-9]+")
_JOB_ID = re.compile(r"(\d{6,})")


def slugify(text: str) -> str:
    """Lowercase ASCII slug. Non-Latin scripts legitimately reduce to ''."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", str(text))
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    return _NON_SLUG.sub("-", ascii_only.lower()).strip("-")


def _cap(slug: str, limit: int) -> str:
    """Cap length deterministically using a hash suffix to avoid collisions.

    A bare truncation caused duplicate entries in career-ops: two runs cut
    the same title at different points. Appending a hash of the full slug
    makes the result deterministic and distinct.
    """
    if len(slug) <= limit:
        return slug
    h = hashlib.sha256(slug.encode()).hexdigest()[:HASH_LEN]
    return slug[: limit - HASH_LEN - 1] + "-" + h


def generate_canonical_key(company: str, title: str, source_url: str | None = None) -> str:
    """Generate a canonical dedup key for a job posting.

    Args:
        company: Company name.
        title: Job title.
        source_url: Optional URL — used as fallback ID for non-Latin titles.

    Returns:
        A deterministic string key like 'google_senior-software-engineer'.
    """
    co_slug = _cap(slugify(company), COMPANY_MAX)
    ti_slug = _cap(slugify(title), TITLE_MAX)

    # If title slugifies to nothing (non-Latin script), fall back to URL-based ID
    if not ti_slug and source_url:
        match = _JOB_ID.search(source_url)
        if match:
            ti_slug = f"id-{match.group(1)}"

    if not ti_slug:
        # Last resort: hash the raw title
        ti_slug = f"h-{hashlib.sha256(title.encode()).hexdigest()[:12]}"

    if not co_slug:
        co_slug = f"h-{hashlib.sha256(company.encode()).hexdigest()[:8]}"

    return f"{co_slug}_{ti_slug}"
