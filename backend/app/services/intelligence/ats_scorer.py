"""ATS score computation — adapted from Resume-Matcher's ats.py.

Computes a 0-100% ATS compatibility score with three weighted sub-scores:
  - keyword_match (55%): overlap between JD keywords and resume
  - skills_coverage (25%): technical skills from JD found in resume
  - section_completeness (20%): presence of essential resume sections
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_WEIGHTS = {
    "keyword_match": 0.55,
    "skills_coverage": 0.25,
    "section_completeness": 0.20,
}

_SECTION_PATTERNS = {
    "summary": ["summary", "objective", "profile", "about"],
    "experience": ["experience", "work history", "employment"],
    "education": ["education", "academic", "degree"],
    "skills": ["skills", "technologies", "competencies", "technical"],
}


def _extract_all_text(data: dict[str, Any] | list | str) -> str:
    """Flatten all string values from a nested structure into one text block."""
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


def _keyword_in_text(keyword: str, text_lower: str) -> bool:
    """Whole-word match against pre-lowercased text."""
    escaped = re.escape(keyword.strip().lower())
    if not escaped:
        return False
    return bool(re.search(rf"(?<!\w){escaped}(?!\w)", text_lower))


def extract_keywords_from_jd(description: str) -> dict[str, list[str]]:
    """Extract required and preferred skills from a job description.

    Simple heuristic extraction — will be enhanced with LLM in Phase 3.
    """
    text_lower = description.lower()

    # Common technical terms to look for
    tech_patterns = [
        r"\b(?:python|java|javascript|typescript|react|angular|vue|node\.?js|go|rust|"
        r"c\+\+|c#|ruby|php|swift|kotlin|scala|r|matlab)\b",
        r"\b(?:aws|azure|gcp|docker|kubernetes|terraform|jenkins|ci/cd|git|linux)\b",
        r"\b(?:sql|nosql|postgresql|mongodb|redis|elasticsearch|kafka|rabbitmq)\b",
        r"\b(?:rest|graphql|grpc|microservices|api|oauth|jwt)\b",
        r"\b(?:machine\s*learning|deep\s*learning|nlp|computer\s*vision|data\s*science|"
        r"tensorflow|pytorch|pandas|numpy|scikit[- ]learn)\b",
        r"\b(?:agile|scrum|kanban|jira|confluence)\b",
    ]

    found_skills: list[str] = []
    for pattern in tech_patterns:
        matches = re.findall(pattern, text_lower)
        found_skills.extend(matches)

    # Deduplicate while preserving order
    seen = set()
    unique_skills: list[str] = []
    for skill in found_skills:
        normalized = skill.strip().lower()
        if normalized not in seen:
            seen.add(normalized)
            unique_skills.append(skill.strip())

    # Split into required vs preferred based on surrounding context
    required: list[str] = []
    preferred: list[str] = []

    for skill in unique_skills:
        # Check if skill appears near "required" or "must" keywords
        skill_pos = text_lower.find(skill.lower())
        if skill_pos >= 0:
            surrounding = text_lower[max(0, skill_pos - 100):skill_pos + 100]
            if any(kw in surrounding for kw in ["required", "must", "essential", "mandatory"]):
                required.append(skill)
            else:
                preferred.append(skill)
        else:
            preferred.append(skill)

    return {
        "required_skills": required,
        "preferred_skills": preferred,
    }


def compute_skills_coverage(resume: dict[str, Any], job_keywords: dict[str, Any]) -> float:
    """Skills coverage score (0-100): how many JD skills appear in resume."""
    jd_skills: list[str] = []
    jd_skills.extend(job_keywords.get("required_skills", []))
    jd_skills.extend(job_keywords.get("preferred_skills", []))

    if not jd_skills:
        return 0.0

    resume_skills = resume.get("skills", [])
    resume_text = _extract_all_text(resume).lower()
    resume_skills_lower = {s.lower() for s in resume_skills if isinstance(s, str)}

    matched = 0
    for skill in jd_skills:
        if not isinstance(skill, str):
            continue
        skill_lower = skill.lower()
        if skill_lower in resume_skills_lower or _keyword_in_text(skill, resume_text):
            matched += 1

    return min(100.0, (matched / len(jd_skills)) * 100)


def compute_section_completeness(resume: dict[str, Any]) -> float:
    """Section completeness score (0-100): key sections present."""
    found = 0

    if resume.get("summary"):
        found += 1
    if resume.get("workExperience"):
        found += 1
    if resume.get("education"):
        found += 1
    if resume.get("skills"):
        found += 1

    if found == 0:
        text = _extract_all_text(resume).lower()
        for patterns in _SECTION_PATTERNS.values():
            if any(p in text for p in patterns):
                found += 1

    return (found / len(_SECTION_PATTERNS)) * 100


def compute_keyword_match(resume: dict[str, Any], job_keywords: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    """Compute keyword match percentage and identify missing/injectable keywords.

    Returns:
        (match_percentage, missing_keywords, injectable_keywords)
    """
    all_keywords: list[str] = []
    all_keywords.extend(job_keywords.get("required_skills", []))
    all_keywords.extend(job_keywords.get("preferred_skills", []))

    if not all_keywords:
        return 100.0, [], []

    resume_text = _extract_all_text(resume).lower()
    resume_skills = {s.lower() for s in resume.get("skills", []) if isinstance(s, str)}

    matched: list[str] = []
    missing: list[str] = []

    for kw in all_keywords:
        if not isinstance(kw, str):
            continue
        kw_lower = kw.lower()
        if kw_lower in resume_skills or _keyword_in_text(kw, resume_text):
            matched.append(kw)
        else:
            missing.append(kw)

    match_pct = (len(matched) / len(all_keywords)) * 100 if all_keywords else 100.0
    return min(100.0, match_pct), missing, []


def compute_ats_score(
    resume: dict[str, Any],
    job_keywords: dict[str, Any],
) -> dict[str, Any]:
    """Compute the full ATS score breakdown.

    Args:
        resume: Structured resume dict.
        job_keywords: Extracted JD keywords dict.

    Returns:
        {overall_score, sub_scores, missing_keywords, injectable_keywords, recommendations}
    """
    kw_pct, missing, injectable = compute_keyword_match(resume, job_keywords)
    sk_score = compute_skills_coverage(resume, job_keywords)
    sec_score = compute_section_completeness(resume)

    overall = (
        kw_pct * _WEIGHTS["keyword_match"]
        + sk_score * _WEIGHTS["skills_coverage"]
        + sec_score * _WEIGHTS["section_completeness"]
    )

    recommendations = _generate_recommendations(kw_pct, sk_score, sec_score, missing, injectable)

    return {
        "overall_score": round(overall, 1),
        "sub_scores": {
            "keyword_match": round(kw_pct, 1),
            "skills_coverage": round(sk_score, 1),
            "section_completeness": round(sec_score, 1),
        },
        "missing_keywords": missing[:10],
        "injectable_keywords": injectable[:10],
        "recommendations": recommendations,
    }


def _generate_recommendations(
    keyword_score: float,
    skills_score: float,
    section_score: float,
    missing_keywords: list[str],
    injectable_keywords: list[str],
) -> list[str]:
    tips: list[str] = []

    if keyword_score < 60 and missing_keywords:
        top = ", ".join(missing_keywords[:5])
        tips.append(f"Add these high-priority missing keywords: {top}.")

    if injectable_keywords:
        top_inj = ", ".join(injectable_keywords[:5])
        tips.append(f"These skills from your master resume could be added: {top_inj}.")

    if skills_score < 60:
        tips.append("Expand your Skills section to include more JD tools and technologies.")

    if section_score < 75:
        tips.append("Ensure your resume has all key sections: Summary, Experience, Education, Skills.")

    if keyword_score >= 80 and skills_score >= 80:
        tips.append("Strong alignment. Quantify achievements with metrics and numbers.")

    if not tips:
        tips.append("Well-aligned with JD. Review for niche certifications or tools.")

    return tips
