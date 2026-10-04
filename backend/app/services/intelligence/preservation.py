"""Anti-hallucination guard — adapted from Resume-Matcher's resume_preservation.py.

Ensures AI-generated resume content never fabricates companies, technologies,
metrics, or other factual claims. Every claim must trace to the master career profile.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

GROUNDING_REVIEW_CODE = "GROUNDING_REVIEW_REQUIRED"
_GROUNDING_REVIEW_THRESHOLD = 0.45

# Fields that must NEVER be modified by AI tailoring
_PROTECTED_FIELDS: dict[str, tuple[str, ...]] = {
    "workExperience": ("id", "title", "company", "location", "years"),
    "education": ("id", "institution", "degree", "years"),
    "projects": ("id", "name", "role", "years", "github", "website"),
}

_NUMBER_RE = re.compile(
    r"(?<![\w.])(?P<currency>[$€£₹])?"
    r"(?P<number>\d[\d,]*(?:\.\d+)?)"
    r"(?:\s*(?P<unit>thousand|million|billion|percent|times|ms|gb|mb|tb|[kmb%x]))?"
    r"(?![A-Za-z])",
    re.IGNORECASE,
)

_TOKEN_RE = re.compile(r"[\w+#./-]+", re.UNICODE)

_STOP_WORDS = frozenset({
    "a", "an", "and", "at", "by", "for", "from", "in", "of", "on", "the", "to", "using", "with",
})


def verify_preservation(
    master_profile: dict[str, Any],
    tailored_content: dict[str, Any],
) -> dict[str, Any]:
    """Verify that AI-tailored content doesn't hallucinate.

    Args:
        master_profile: The user's original career profile (source of truth).
        tailored_content: The AI-modified resume content.

    Returns:
        {
            "status": "passed" | "failed" | "review_required",
            "violations": [...],
            "grounding_score": float,
            "protected_fields_ok": bool,
        }
    """
    violations: list[dict[str, str]] = []

    # 1. Check protected fields haven't been modified
    protected_ok = _check_protected_fields(master_profile, tailored_content, violations)

    # 2. Verify all numbers/metrics in tailored content exist in master
    _check_numbers(master_profile, tailored_content, violations)

    # 3. Verify company names exist in master
    _check_company_names(master_profile, tailored_content, violations)

    # 4. Compute grounding score (token overlap with master)
    grounding_score = _compute_grounding_score(master_profile, tailored_content)

    # Determine status
    if violations:
        status = "failed"
    elif grounding_score < _GROUNDING_REVIEW_THRESHOLD:
        status = "review_required"
        violations.append({
            "type": "low_grounding",
            "message": f"Grounding score {grounding_score:.2f} is below threshold {_GROUNDING_REVIEW_THRESHOLD}",
        })
    else:
        status = "passed"

    return {
        "status": status,
        "violations": violations,
        "grounding_score": round(grounding_score, 3),
        "protected_fields_ok": protected_ok,
    }


def _check_protected_fields(
    master: dict[str, Any],
    tailored: dict[str, Any],
    violations: list[dict[str, str]],
) -> bool:
    """Ensure protected fields (company, title, etc.) match the master exactly."""
    all_ok = True

    for section_key, protected in _PROTECTED_FIELDS.items():
        master_entries = master.get(section_key, [])
        tailored_entries = tailored.get(section_key, [])

        if not isinstance(master_entries, list) or not isinstance(tailored_entries, list):
            continue

        for t_entry in tailored_entries:
            if not isinstance(t_entry, dict):
                continue

            # Find matching master entry
            m_entry = _find_matching_entry(t_entry, master_entries, section_key)
            if not m_entry:
                violations.append({
                    "type": "ungrounded_entry",
                    "section": section_key,
                    "message": f"Entry not found in master profile: {_entry_summary(t_entry)}",
                })
                all_ok = False
                continue

            # Check each protected field
            for field in protected:
                master_val = _normalized(m_entry.get(field))
                tailored_val = _normalized(t_entry.get(field))
                if master_val and tailored_val and master_val != tailored_val:
                    violations.append({
                        "type": "protected_field_modified",
                        "section": section_key,
                        "field": field,
                        "master": str(m_entry.get(field)),
                        "tailored": str(t_entry.get(field)),
                    })
                    all_ok = False

    return all_ok


def _check_numbers(
    master: dict[str, Any],
    tailored: dict[str, Any],
    violations: list[dict[str, str]],
) -> None:
    """Verify every number in tailored content exists in master profile."""
    master_text = _extract_all_text(master).lower()
    master_numbers = {m.group("number").replace(",", "") for m in _NUMBER_RE.finditer(master_text)}

    tailored_text = _extract_all_text(tailored).lower()
    for match in _NUMBER_RE.finditer(tailored_text):
        number = match.group("number").replace(",", "")
        if number not in master_numbers and number not in ("0", "1", "2", "3"):
            context = tailored_text[max(0, match.start() - 30):match.end() + 30]
            violations.append({
                "type": "ungrounded_number",
                "number": number,
                "context": context.strip(),
            })


def _check_company_names(
    master: dict[str, Any],
    tailored: dict[str, Any],
    violations: list[dict[str, str]],
) -> None:
    """Verify company names in tailored content exist in master."""
    master_companies = set()
    for entry in master.get("workExperience", []):
        if isinstance(entry, dict) and entry.get("company"):
            master_companies.add(_normalized(entry["company"]))

    for entry in tailored.get("workExperience", []):
        if isinstance(entry, dict) and entry.get("company"):
            company = _normalized(entry["company"])
            if company and company not in master_companies:
                violations.append({
                    "type": "unknown_company",
                    "company": entry["company"],
                    "message": f"Company '{entry['company']}' not found in master profile",
                })


def _compute_grounding_score(master: dict[str, Any], tailored: dict[str, Any]) -> float:
    """Token overlap between master and tailored content (0.0 - 1.0)."""
    master_tokens = _tokenize(_extract_all_text(master))
    tailored_tokens = _tokenize(_extract_all_text(tailored))

    if not tailored_tokens:
        return 1.0

    overlap = master_tokens & tailored_tokens
    return len(overlap) / len(tailored_tokens)


def _find_matching_entry(
    entry: dict[str, Any],
    candidates: list[dict[str, Any]],
    section_key: str,
) -> dict[str, Any] | None:
    """Find the best matching entry in candidates using sequence matching."""
    entry_text = _entry_summary(entry)
    best_match = None
    best_ratio = 0.0

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        candidate_text = _entry_summary(candidate)
        ratio = SequenceMatcher(None, entry_text, candidate_text).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = candidate

    return best_match if best_ratio > 0.5 else None


def _entry_summary(entry: dict[str, Any]) -> str:
    """Build a summary string for an entry for matching."""
    parts = []
    for key in ("company", "title", "institution", "degree", "name", "role"):
        val = entry.get(key)
        if val:
            parts.append(str(val))
    return " ".join(parts).lower()


def _normalized(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def _extract_all_text(data: Any) -> str:
    parts: list[str] = []

    def _walk(obj: Any) -> None:
        if isinstance(obj, str):
            parts.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)
        elif isinstance(obj, dict):
            for v in obj.values():
                _walk(v)

    _walk(data)
    return " ".join(parts)


def _tokenize(text: str) -> set[str]:
    tokens = set()
    for match in _TOKEN_RE.finditer(text.lower()):
        token = match.group()
        if token not in _STOP_WORDS and len(token) > 1:
            tokens.add(token)
    return tokens
